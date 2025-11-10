from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Iterable, Optional, Set, Union, List

from core.registry import register_adapter

from adapters.base import Edge, Frame
from adapters.curriculum.extractor import extract
from adapters.curriculum.preprocess import CurriculumPreprocessor
from configs.datasets import CurriculumDatasetConfig, load_dataset_config


@register_adapter("curriculum_stream")
class CurriculumStream:
    def __init__(
        self,
        path: Optional[str] = None,
        *,
        config: Union[str, os.PathLike[str], CurriculumDatasetConfig, None] = None,
        scramble: bool = False,
        random_shift: Optional[int] = None,
        stop_nodes: Set[str] | None = None,
        stop_patterns: Iterable[str] | None = None,
    ):
        cfg = self._resolve_config(config)
        if path is None and cfg is not None:
            path = str(cfg.builder.output)

        if path is None:
            raise ValueError("curriculum_stream requires path to a curriculum zip")
        if not os.path.exists(path):
            raise FileNotFoundError(path)

        raw = extract(path)
        pre = CurriculumPreprocessor(
            config=cfg.preprocessor if cfg else None,
            stop_nodes=stop_nodes,
            stop_patterns=stop_patterns,
        )
        processed = pre.process(raw)

        self.path = path
        self.scramble = scramble
        self.random_shift = random_shift

        self.nodes: Dict[int, str] = processed.nodes
        self.obs_steps = processed.obs_steps
        self.true_steps = processed.true_steps
        self._steps = sorted(set(self.obs_steps.keys()) | set(self.true_steps.keys()))
        self._idx = 0

        self._meta = dict(processed.meta)
        self._meta.setdefault("steps", len(self._steps))
        self._meta.setdefault("nodes", len(self.nodes))
        self._meta.setdefault("adapter", "curriculum_stream")
        # cache course_id if available for gating behavior
        self.course_id: str = str(self._meta.get("course_id") or Path(str(path)).stem)

        # Derived weights and per-step features so signals can incorporate resource influence
        self._resource_features_enabled = self._feature_enabled_for_course(self.course_id)
        self.node_weights: Dict[int, float] = (
            self._compute_node_weights(self.nodes) if self._resource_features_enabled else {nid: 1.0 for nid in self.nodes}
        )
        self._step_nodes: Dict[int, Set[int]] = {
            step: {n for (u, v) in edges for n in (u, v)} for step, edges in self.obs_steps.items()
        }
        self._step_features: Dict[int, Dict[str, float]] = self._compute_step_features() if self._resource_features_enabled else {}

    # ------------------------------------------------------------------

    def next_obs(self) -> Frame:
        if self._idx >= len(self._steps):
            return set()
        step = self._steps[self._idx]
        obs = set(self.obs_steps.get(step, set()))
        if self.scramble and obs:
            obs = self._scramble(obs)
        self._idx += 1
        return obs

    def peek_truth(self, horizon: int) -> Optional[Frame]:
        if not self.true_steps:
            return None
        idx = self._idx - 1 + horizon
        if idx < 0 or idx >= len(self._steps):
            return None
        step = self._steps[idx]
        if self.random_shift is not None and self._steps:
            step = self._steps[(idx + self.random_shift) % len(self._steps)]
        return set(self.true_steps.get(step, set()))

    def has_more(self) -> bool:
        return self._idx < len(self._steps)

    def meta(self) -> Dict[str, object]:
        return dict(self._meta)

    def node_label(self, node_id: int) -> str:
        return self.nodes.get(node_id, str(node_id))

    # Expose current step id for engine bookkeeping
    def current_step(self) -> Optional[int]:
        if not self._steps:
            return None
        # After next_obs() increments _idx, current step is the one just consumed
        idx = max(0, min(len(self._steps) - 1, self._idx - 1))
        return self._steps[idx]

    # Provide per-step features so SignalComputer can use weighted mass and continuity
    def get_step_features(self, step_id: int) -> Dict[str, float]:
        # Only expose features if enabled for this course
        if not self._resource_features_enabled:
            return {}
        return dict(self._step_features.get(step_id, {}))

    # ------------------------------------------------------------------

    def _scramble(self, edges: Frame) -> Frame:
        nodes = {n for e in edges for n in e}
        perm = {n: p for n, p in zip(sorted(nodes), reversed(sorted(nodes)))}
        return {(perm.get(u, u), perm.get(v, v)) for (u, v) in edges}

    @staticmethod
    def _resolve_config(
        config: Union[str, os.PathLike[str], CurriculumDatasetConfig, None]
    ) -> Optional[CurriculumDatasetConfig]:
        if config is None:
            return None
        if isinstance(config, CurriculumDatasetConfig):
            return config
        resolved = load_dataset_config(Path(config))
        if not isinstance(resolved, CurriculumDatasetConfig):
            raise ValueError(f"Config {config!r} is not a curriculum dataset config")
        return resolved

    # ------------------------- internals -------------------------

    @staticmethod
    def _is_resource_label(label: str) -> bool:
        lower = (label or "").lower()
        return ("lecture notes" in lower) or ("notes" in lower) or ("resource::" in label)

    def _feature_enabled_for_course(self, course_id: str) -> bool:
        import os as _os
        flag = _os.environ.get("AXIOM_RESOURCE_FEATURE_TEST", "0")
        if flag in ("1", "true", "TRUE", "yes"):
            return True
        wl = _os.environ.get("AXIOM_RESOURCE_FEATURE_COURSES", "")
        if not wl:
            try:
                has_segments = any("[segment" in (lbl or "").lower() for lbl in self.nodes.values())
                if has_segments and len(self._steps) <= 30:
                    return True
            except Exception:
                pass
            return False
        allow = {c.strip() for c in wl.split(",") if c.strip()}
        return course_id in allow or "*" in allow or "all" in allow
    def _compute_node_weights(self, nodes: Dict[int, str]) -> Dict[int, float]:
        import os as _os
        # Global scale for sweeps
        g_scale = float(_os.environ.get("AXIOM_WEIGHT_SCALE", "1.0") or 1.0)
        res_scale = float(_os.environ.get("AXIOM_RESOURCE_W_SCALE", str(g_scale)) or g_scale)
        lec_scale = float(_os.environ.get("AXIOM_LECTURE_W_SCALE", str(g_scale)) or g_scale)
        pset_scale = float(_os.environ.get("AXIOM_PSET_W_SCALE", "1.0") or 1.0)

        weights: Dict[int, float] = {}
        for nid, label in nodes.items():
            text = (label or "").lower()
            w = 1.0
            if self._is_resource_label(label):
                w = 5.0 * res_scale
            elif ("lecture notes" in text) or ("lecture" in text and "part" in text):
                w = 3.5 * lec_scale
            elif "segment" in text:
                w = 3.0 * res_scale
            elif any(tok in text for tok in ("problem set", "pset", "exam", "quiz")):
                w = 1.25 * pset_scale
            weights[nid] = float(w)
        return weights

    def _compute_step_features(self) -> Dict[int, Dict[str, float]]:
        features: Dict[int, Dict[str, float]] = {}
        # Use per-step node sets (not cumulative) for a stable, adapter-local continuity signal
        prev_nodes: Optional[Set[int]] = None
        for step in self._steps:
            nodes = self._step_nodes.get(step, set())
            uniq = len(nodes)
            mass = sum(self.node_weights.get(n, 1.0) for n in nodes)
            # Weighted continuity (node-set Jaccard with previous step)
            if prev_nodes is not None:
                inter = sum(self.node_weights.get(n, 1.0) for n in (nodes & prev_nodes))
                union = sum(self.node_weights.get(n, 1.0) for n in (nodes | prev_nodes)) or 1.0
                ted = 1.0 - (inter / union)
            else:
                ted = 0.0
            features[step] = {
                "unique_node_count": float(uniq),
                "weighted_node_mass": float(mass),
                "ted": float(max(0.0, min(1.0, ted))),
            }
            prev_nodes = nodes
        return features




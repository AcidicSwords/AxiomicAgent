from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Iterable, Optional, Set, Union

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
        self.step_features = processed.step_features
        self.node_tags = processed.node_tags
        self.node_weights = processed.node_weights
        self._steps = sorted(set(self.obs_steps.keys()) | set(self.true_steps.keys()))
        self._idx = 0
        self._last_step: Optional[int] = None

        self._meta = dict(processed.meta)
        self._meta.setdefault("steps", len(self._steps))
        self._meta.setdefault("nodes", len(self.nodes))
        self._meta.setdefault("adapter", "curriculum_stream")

    # ------------------------------------------------------------------

    def next_obs(self) -> Frame:
        if self._idx >= len(self._steps):
            return set()
        step = self._steps[self._idx]
        obs = set(self.obs_steps.get(step, set()))
        if self.scramble and obs:
            obs = self._scramble(obs)
        self._last_step = step
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

    def current_step(self) -> Optional[int]:
        return self._last_step

    def get_step_features(self, step: int) -> Dict[str, object]:
        return self.step_features.get(step, {})

    def meta(self) -> Dict[str, object]:
        return dict(self._meta)

    def node_label(self, node_id: int) -> str:
        return self.nodes.get(node_id, str(node_id))

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

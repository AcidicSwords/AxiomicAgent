from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Set, Tuple

from core.heads import SignalHead, StepFrame

Edge = Tuple[int, int]


class MonteCarloHead(SignalHead):
    """Estimate robustness/uncertainty of q and TED via lightweight Monte Carlo."""

    name = "monte_carlo"

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        super().__init__(config)
        cfg = (config or {}).get("monte_carlo", {})
        self.num_samples = int(cfg.get("num_samples", 16))
        self.edge_dropout = float(cfg.get("edge_dropout", 0.1))
        self.weight_jitter = float(cfg.get("weight_jitter", 0.1))
        self._step_uncertainty: List[Dict[str, float]] = []
        self._rng = random.Random(cfg.get("seed"))
        self._prev_edges_cache: Optional[Set[Edge]] = None

    def init_course(self, course_id: str, meta: Dict[str, Any]) -> None:
        self._step_uncertainty = []
        self._prev_edges_cache = None

    def per_step(self, frame: StepFrame, base_signals: Dict[str, float]) -> Dict[str, Any]:
        prev_edges = frame.prev_cumulative or self._prev_edges_cache or set()
        curr_edges = frame.cumulative_edges
        node_weights = frame.node_weights or {}

        q_samples: List[float] = []
        ted_samples: List[float] = []

        for _ in range(self.num_samples):
            jitter_weights = self._jitter_weights(node_weights)
            sampled_prev = self._drop_edges(prev_edges, self.edge_dropout)
            sampled_curr = self._drop_edges(curr_edges, self.edge_dropout)
            q_samples.append(self._compute_q(sampled_curr, jitter_weights))
            ted_samples.append(self._compute_ted(sampled_prev, sampled_curr))

        q_mean, q_std = self._stats(q_samples)
        ted_mean, ted_std = self._stats(ted_samples)

        self._step_uncertainty.append({"q_std": q_std, "ted_std": ted_std})
        self._prev_edges_cache = set(curr_edges)

        return {
            "q_mc_mean": q_mean,
            "q_mc_std": q_std,
            "ted_mc_mean": ted_mean,
            "ted_mc_std": ted_std,
        }

    def finalize_course(self) -> Dict[str, Any]:
        if not self._step_uncertainty:
            return {}
        avg_q_std = sum(entry["q_std"] for entry in self._step_uncertainty) / len(self._step_uncertainty)
        avg_ted_std = sum(entry["ted_std"] for entry in self._step_uncertainty) / len(self._step_uncertainty)
        return {
            "avg_q_mc_std": avg_q_std,
            "avg_ted_mc_std": avg_ted_std,
        }

    def _drop_edges(self, edges: Set[Edge], rate: float) -> Set[Edge]:
        if not edges or rate <= 0:
            return set(edges)
        kept = {edge for edge in edges if self._rng.random() > rate}
        if not kept and edges:
            # always keep at least one edge to avoid empty graph pathologies
            kept.add(self._rng.choice(tuple(edges)))
        return kept

    def _jitter_weights(self, weights: Dict[int, float]) -> Dict[int, float]:
        if not weights or self.weight_jitter <= 0:
            return dict(weights)
        jittered: Dict[int, float] = {}
        for nid, value in weights.items():
            scale = 1.0 + self._rng.uniform(-self.weight_jitter, self.weight_jitter)
            jittered[nid] = max(0.0, value * scale)
        return jittered

    @staticmethod
    def _compute_q(edges: Set[Edge], weights: Dict[int, float]) -> float:
        if not edges:
            return 0.0
        seen: Set[int] = set()
        total = 0.0
        for src, dst in edges:
            for nid in (src, dst):
                if nid not in seen:
                    seen.add(nid)
                    total += weights.get(nid, 1.0)
        if not seen:
            return 0.0
        denom = max(1.0, len(seen) * 2.0)
        return min(1.0, total / denom)

    @staticmethod
    def _compute_ted(prev_edges: Set[Edge], curr_edges: Set[Edge]) -> float:
        if not prev_edges and not curr_edges:
            return 0.0
        intersection = len(prev_edges & curr_edges)
        union = len(prev_edges | curr_edges)
        if union == 0:
            return 0.0
        value = 1.0 - (intersection / union)
        return max(0.0, min(1.0, value))

    @staticmethod
    def _stats(values: List[float]) -> Tuple[float, float]:
        if not values:
            return 0.0, 0.0
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        return mean, variance ** 0.5

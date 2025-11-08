from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Dict, Optional, Set, Tuple

Edge = Tuple[int, int]


@dataclass(frozen=True)
class StepFrame:
    """Lightweight container describing the current step for signal heads."""

    t: int
    step_id: int
    obs_edges: Set[Edge]
    cumulative_edges: Set[Edge]
    prev_cumulative: Optional[Set[Edge]]
    node_weights: Dict[int, float]
    step_features: Dict[str, Any]

    def with_replacements(
        self,
        *,
        obs_edges: Optional[Set[Edge]] = None,
        cumulative_edges: Optional[Set[Edge]] = None,
        prev_cumulative: Optional[Set[Edge]] = None,
        node_weights: Optional[Dict[int, float]] = None,
    ) -> "StepFrame":
        """Return a copy with selected fields replaced."""
        return replace(
            self,
            obs_edges=obs_edges if obs_edges is not None else self.obs_edges,
            cumulative_edges=cumulative_edges if cumulative_edges is not None else self.cumulative_edges,
            prev_cumulative=prev_cumulative if prev_cumulative is not None else self.prev_cumulative,
            node_weights=node_weights if node_weights is not None else self.node_weights,
        )


class SignalHead:
    """Base class for pluggable signal heads."""

    name = "base"

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        self.config = config or {}

    def init_course(self, course_id: str, meta: Dict[str, Any]) -> None:  # pragma: no cover - optional override
        pass

    def per_step(self, frame: StepFrame, base_signals: Dict[str, float]) -> Dict[str, Any]:  # pragma: no cover
        return {}

    def finalize_course(self) -> Dict[str, Any]:  # pragma: no cover
        return {}

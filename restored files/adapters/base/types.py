from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Set, Tuple

Edge = Tuple[int, int]
Frame = Set[Edge]


@dataclass(slots=True)
class RawStream:
    nodes: Dict[int, Dict[str, Any]]
    obs_steps: Dict[int, Frame]
    true_steps: Dict[int, Frame]
    meta: Dict[str, object]
    step_features: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    node_tags: Dict[int, Set[str]] = field(default_factory=dict)
    node_weights: Dict[int, float] = field(default_factory=dict)


@dataclass(slots=True)
class ProcessedStream:
    nodes: Dict[int, Dict[str, Any]]
    obs_steps: Dict[int, Frame]
    true_steps: Dict[int, Frame]
    meta: Dict[str, object]
    step_features: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    node_tags: Dict[int, Set[str]] = field(default_factory=dict)
    node_weights: Dict[int, float] = field(default_factory=dict)

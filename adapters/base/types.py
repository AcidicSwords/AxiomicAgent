from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Set, Tuple


Edge = Tuple[int, int]
Frame = Set[Edge]


@dataclass(slots=True)
class RawStream:
    nodes: Dict[int, str]
    obs_steps: Dict[int, Frame]
    true_steps: Dict[int, Frame]
    meta: Dict[str, object]


@dataclass(slots=True)
class ProcessedStream:
    nodes: Dict[int, str]
    obs_steps: Dict[int, Frame]
    true_steps: Dict[int, Frame]
    meta: Dict[str, object]

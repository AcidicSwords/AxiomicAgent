from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Set, Tuple

from adapters.base import Frame

Edge = Tuple[int, int]


@dataclass
class PolicyConfig:
    max_edges: Optional[int] = None
    max_nodes: Optional[int] = None
    sticky_fraction: float = 0.5


class Policy:
    def __init__(self, config: Optional[PolicyConfig] = None) -> None:
        self.config = config or PolicyConfig()

    def step(
        self,
        *,
        step_index: int,
        prev_pred: Optional[Frame],
        obs_t: Frame,
        signals: Dict[str, float],
        core_config: Dict[str, object],
    ) -> Frame:
        raise NotImplementedError


class IdentityPolicy(Policy):
    def step(
        self,
        *,
        step_index: int,
        prev_pred: Optional[Frame],
        obs_t: Frame,
        signals: Dict[str, float],
        core_config: Dict[str, object],
    ) -> Frame:
        return set(obs_t)


class CapacityPolicy(Policy):
    def step(
        self,
        *,
        step_index: int,
        prev_pred: Optional[Frame],
        obs_t: Frame,
        signals: Dict[str, float],
        core_config: Dict[str, object],
    ) -> Frame:
        max_edges = self.config.max_edges
        if not max_edges or max_edges <= 0:
            return set(obs_t)

        prev = prev_pred or set()
        sticky_space = int(max_edges * self.config.sticky_fraction)
        nonsticky_space = max_edges - sticky_space

        intersection = prev & obs_t
        new_edges = obs_t - prev

        selected: Set[Edge] = set()

        for edge in sorted(intersection):
            if len(selected) >= sticky_space:
                break
            selected.add(edge)

        for edge in sorted(new_edges):
            if len(selected) >= max_edges:
                break
            selected.add(edge)

        if len(selected) < max_edges:
            for edge in sorted(intersection):
                if len(selected) >= max_edges:
                    break
                selected.add(edge)

        if self.config.max_nodes:
            selected = self._enforce_node_capacity(selected)

        return selected

    def _enforce_node_capacity(self, edges: Set[Edge]) -> Set[Edge]:
        max_nodes = self.config.max_nodes or 0
        if max_nodes <= 0:
            return edges

        selected: Set[Edge] = set()
        node_counts: Dict[int, int] = {}

        for edge in edges:
            u, v = edge
            if node_counts.get(u, 0) >= max_nodes and node_counts.get(v, 0) >= max_nodes:
                continue
            selected.add(edge)
            node_counts[u] = node_counts.get(u, 0) + 1
            node_counts[v] = node_counts.get(v, 0) + 1

        return selected

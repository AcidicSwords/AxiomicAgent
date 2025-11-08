from __future__ import annotations

import math
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

from adapters.base import Frame

Edge = Tuple[int, int]
StepFeatures = Dict[str, Any]
CoreConfig = Dict[str, Any]


@dataclass
class SignalConfig:
    compute_spread: bool = False
    compute_locality: bool = False


@dataclass
class Signals:
    q: float
    ted: float
    stability: float
    ted_delta: Optional[float]
    spread: Optional[float] = None
    locality_nodes: Optional[List[int]] = None


class SignalComputer:
    def __init__(self, config: Optional[SignalConfig] = None) -> None:
        self.config = config or SignalConfig()
        self._prev_ted: Optional[float] = None

    def compute(
        self,
        *,
        step_index: int,
        obs_t: Frame,
        prev_obs: Optional[Frame],
        step_features: StepFeatures,
        core_config: CoreConfig,
    ) -> Signals:
        raise NotImplementedError


class DefaultSignalComputer(SignalComputer):
    def compute(
        self,
        *,
        step_index: int,
        obs_t: Frame,
        prev_obs: Optional[Frame],
        step_features: StepFeatures,
        core_config: CoreConfig,
    ) -> Signals:
        q = step_features.get("quality")
        if q is None:
            q = self._fallback_quality(obs_t, step_features)

        ted_feature = step_features.get("ted")
        if isinstance(ted_feature, (int, float)) and not math.isnan(float(ted_feature)):
            ted = float(ted_feature)
        else:
            ted = self._fallback_ted(obs_t, prev_obs)

        stability = step_features.get("stability")
        if stability is None:
            stability = max(0.0, min(1.0, 1.0 - ted))

        spread = None
        locality = None

        if self.config.compute_spread:
            components = self._connected_components(obs_t)
            spread = self._compute_spread(components)

        if self.config.compute_locality:
            locality = self._locality_nodes(obs_t, prev_obs, top_k=5)

        ted_delta = None if self._prev_ted is None else round(ted - self._prev_ted, 3)
        self._prev_ted = ted

        return Signals(
            q=round(float(q), 3),
            ted=round(float(ted), 3),
            stability=round(float(stability), 3),
            ted_delta=ted_delta,
            spread=spread,
            locality_nodes=locality,
        )

    @staticmethod
    def _fallback_quality(obs: Frame, step_features: Optional[StepFeatures] = None) -> float:
        if not obs:
            return 0.0
        if step_features:
            mass = step_features.get("weighted_node_mass")
            unique = step_features.get("unique_node_count")
            try:
                mass_val = float(mass)
                unique_val = float(unique)
            except (TypeError, ValueError):
                mass_val = None
                unique_val = None
            if mass_val is not None and unique_val is not None and unique_val > 0:
                denom = max(1.0, unique_val * 2.0)
                return min(1.0, mass_val / denom)
        nodes = {node for edge in obs for node in edge}
        return min(1.0, len(nodes) / 25.0)

    @staticmethod
    def _fallback_ted(obs: Frame, prev_obs: Optional[Frame]) -> float:
        if prev_obs is None:
            return 0.0
        if not obs and not prev_obs:
            return 0.0
        intersection = len(obs & prev_obs)
        union = len(obs | prev_obs)
        if union == 0:
            return 0.0
        value = 1.0 - intersection / union
        return max(0.0, min(1.0, value))

    @staticmethod
    def _connected_components(edges: Frame) -> list[Set[int]]:
        if not edges:
            return []
        adj: Dict[int, Set[int]] = defaultdict(set)
        for u, v in edges:
            adj[u].add(v)
            adj[v].add(u)

        visited: Set[int] = set()
        components: list[Set[int]] = []

        for node in adj:
            if node in visited:
                continue
            queue = deque([node])
            component: Set[int] = set()
            while queue:
                current = queue.popleft()
                if current in visited:
                    continue
                visited.add(current)
                component.add(current)
                queue.extend(adj[current] - visited)
            components.append(component)

        return components

    @staticmethod
    def _compute_spread(components: list[Set[int]]) -> float:
        if not components:
            return 0.0
        total = sum(len(comp) for comp in components)
        if total == 0 or len(components) == 1:
            return 0.0
        probabilities = [len(comp) / total for comp in components]
        entropy = -sum(p * math.log(p) for p in probabilities if p > 0)
        return round(entropy / math.log(len(probabilities)), 3) if len(probabilities) > 1 else 0.0

    @staticmethod
    def _locality_nodes(
        obs_t: Frame,
        prev_obs: Optional[Frame],
        *,
        top_k: int = 5,
    ) -> list[int]:
        if prev_obs is None:
            return []

        def degrees(edges: Frame) -> Dict[int, int]:
            deg: Dict[int, int] = defaultdict(int)
            for u, v in edges:
                deg[u] += 1
                deg[v] += 1
            return deg

        current_deg = degrees(obs_t)
        previous_deg = degrees(prev_obs)
        nodes = set(current_deg) | set(previous_deg)
        deltas = {
            node: abs(current_deg.get(node, 0) - previous_deg.get(node, 0))
            for node in nodes
        }
        ordered = sorted(nodes, key=lambda n: deltas[n], reverse=True)
        return ordered[:top_k]

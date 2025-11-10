from __future__ import annotations

from typing import Dict, Iterable, List, Set

from configs.datasets import ConversationPreprocessorConfig

from adapters.base import Edge, Frame, ProcessedStream, RawStream

STOP_TERMS = {
    "the", "and", "or", "but", "if", "in", "on", "at", "to", "for",
    "with", "a", "an", "of", "is", "it", "this", "that", "be", "are",
    "as", "by", "from", "was", "were", "do", "does", "did", "about",
    "into", "out", "up", "down", "off", "over", "under", "than", "so",
    "such", "just", "well", "very", "have", "has", "had", "we", "you",
    "they", "them", "their", "our", "i", "me", "my", "your", "not",
}


class ConversationPreprocessor:
    def __init__(
        self,
        config: ConversationPreprocessorConfig | None = None,
        *,
        stop_terms: Set[str] | None = None,
        min_length: int | None = None,
        max_degree: int | None = None,
    ):
        cfg = config or ConversationPreprocessorConfig()
        merged_stop_terms = stop_terms if stop_terms is not None else set(cfg.stop_terms or [])
        if not merged_stop_terms:
            merged_stop_terms = set(STOP_TERMS)
        else:
            merged_stop_terms = set(merged_stop_terms) | {t.lower() for t in STOP_TERMS}
        self.stop_terms = {t.lower() for t in merged_stop_terms}
        self.min_length = int(min_length if min_length is not None else cfg.min_length)
        self.max_degree = int(max_degree if max_degree is not None else cfg.degree_cap)

    def process(self, raw: RawStream) -> ProcessedStream:
        nodes = {nid: label for nid, label in raw.nodes.items() if self._keep_term(label)}

        obs_steps: Dict[int, Frame] = {}
        for step, edges in raw.obs_steps.items():
            filtered = self._cap_step([edge for edge in edges if self._keep_edge(edge, nodes)])
            obs_steps[step] = filtered

        true_steps: Dict[int, Frame] = {}
        for step, edges in raw.true_steps.items():
            filtered = self._cap_step([edge for edge in edges if self._keep_edge(edge, nodes)])
            true_steps[step] = filtered

        used_nodes: Set[int] = set()
        for step_edges in obs_steps.values():
            for u, v in step_edges:
                used_nodes.update([u, v])
        for step_edges in true_steps.values():
            for u, v in step_edges:
                used_nodes.update([u, v])

        nodes = {nid: label for nid, label in nodes.items() if nid in used_nodes}

        meta = dict(raw.meta)
        meta.setdefault("filter", "conversation")
        meta.setdefault("stop_terms", sorted(self.stop_terms))
        return ProcessedStream(nodes=nodes, obs_steps=obs_steps, true_steps=true_steps, meta=meta)

    def _keep_term(self, label: str) -> bool:
        if not label:
            return False
        term = label.lower()
        if term in self.stop_terms:
            return False
        if len(term) < self.min_length:
            return False
        return True

    def _keep_edge(self, edge: Edge, nodes: Dict[int, str]) -> bool:
        u, v = edge
        if u == v:
            return False
        if u not in nodes or v not in nodes:
            return False
        return True

    def _cap_step(self, edges: Iterable[Edge]) -> Frame:
        deg: Dict[int, int] = {}
        result: List[Edge] = []
        for u, v in edges:
            if deg.get(u, 0) >= self.max_degree:
                continue
            if deg.get(v, 0) >= self.max_degree:
                continue
            result.append((u, v))
            deg[u] = deg.get(u, 0) + 1
            deg[v] = deg.get(v, 0) + 1
        return set(result)

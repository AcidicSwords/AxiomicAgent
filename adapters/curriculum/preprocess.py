from __future__ import annotations

import re
from typing import Dict, Iterable, List, Set

from adapters.base import Edge, Frame, ProcessedStream, RawStream
from configs.datasets import CurriculumPreprocessorConfig, CurriculumTypeRule

DEFAULT_STOP_NODES = {
    "Contact Us",
    "Browse Course Material",
    "Help & FAQs",
    "About OCW",
    "Give Now",
    "Syllabus",
    "Calendar",
    "Recitations",
    "Download",
    "Transcript",
    "Video",
    "Lecture Notes",
}

DEFAULT_STOP_PATTERNS = [
    r"^lec\d+(\.jpg|\.png|\.mp4|\.srt)$",
    r".*\.srt$",
    r"^\s*$",
]

DEFAULT_TYPE_WEIGHTS = {
    "exam": 0.70,
    "pset": 0.70,
    "concept": 1.00,
    "theorem": 1.00,
    "definition": 1.00,
    "nav": 0.05,
    "media": 0.05,
    "person": 0.30,
    "unknown": 0.50,
}

DEFAULT_KEEP_THRESHOLD = 0.10
DEFAULT_TOPK_PER_NODE = 50


class CurriculumPreprocessor:
    def __init__(
        self,
        config: CurriculumPreprocessorConfig | None = None,
        *,
        stop_nodes: Set[str] | None = None,
        stop_patterns: Iterable[str] | None = None,
        type_weights: Dict[str, float] | None = None,
        keep_threshold: float | None = None,
        topk_per_node: int | None = None,
    ):
        cfg = config or CurriculumPreprocessorConfig(
            stop_nodes=list(DEFAULT_STOP_NODES),
            regex_patterns=list(DEFAULT_STOP_PATTERNS),
            type_rules=[],
            keep_threshold=DEFAULT_KEEP_THRESHOLD,
            topk_per_node=DEFAULT_TOPK_PER_NODE,
        )
        merged_stop_nodes = stop_nodes if stop_nodes is not None else set(cfg.stop_nodes or [])
        if not merged_stop_nodes:
            merged_stop_nodes = set(DEFAULT_STOP_NODES)
        else:
            merged_stop_nodes = set(merged_stop_nodes) | {s for s in DEFAULT_STOP_NODES}
        self.stop_nodes = set(merged_stop_nodes)
        self.stop_nodes_lower = {s.lower() for s in self.stop_nodes}

        pattern_values = list(stop_patterns if stop_patterns is not None else (cfg.regex_patterns or []))
        if not pattern_values:
            pattern_values = list(DEFAULT_STOP_PATTERNS)
        self.stop_re = [re.compile(p, re.I) for p in pattern_values]

        base_type_weights = dict(DEFAULT_TYPE_WEIGHTS)
        self.custom_rules: List[CurriculumTypeRule] = list(cfg.type_rules or [])
        for rule in self.custom_rules:
            base_type_weights[rule.type] = rule.weight
        if type_weights:
            base_type_weights.update(type_weights)
        self.type_weights = base_type_weights
        self.keep_threshold = float(
            keep_threshold if keep_threshold is not None else cfg.keep_threshold or DEFAULT_KEEP_THRESHOLD
        )
        self.topk_per_node = int(topk_per_node if topk_per_node is not None else cfg.topk_per_node or DEFAULT_TOPK_PER_NODE)

    def process(self, raw: RawStream) -> ProcessedStream:
        nodes = dict(raw.nodes)
        node_type = {nid: self._infer_type(label) for nid, label in nodes.items()}

        obs_steps: Dict[int, Frame] = {}
        for step, edges in raw.obs_steps.items():
            filtered = self._cap_step([edge for edge in edges if self._keep_edge(edge, nodes, node_type)])
            obs_steps[step] = self._augment_resource_edges(filtered, nodes, node_type)

        true_steps: Dict[int, Frame] = {}
        for step, edges in raw.true_steps.items():
            filtered = self._cap_step([edge for edge in edges if self._keep_edge(edge, nodes, node_type)])
            true_steps[step] = self._augment_resource_edges(filtered, nodes, node_type)

        used_nodes: Set[int] = set()
        for step_edges in obs_steps.values():
            for u, v in step_edges:
                used_nodes.add(u)
                used_nodes.add(v)
        for step_edges in true_steps.values():
            for u, v in step_edges:
                used_nodes.add(u)
                used_nodes.add(v)

        nodes = {nid: label for nid, label in nodes.items() if nid in used_nodes}

        meta = dict(raw.meta)
        meta.setdefault("filter", "curriculum")
        meta.setdefault("stop_nodes", sorted(self.stop_nodes))
        return ProcessedStream(nodes=nodes, obs_steps=obs_steps, true_steps=true_steps, meta=meta)


    def _augment_resource_edges(self, frame: Frame, nodes: Dict[int, str], node_type_map: Dict[int, str]) -> Frame:
            """Link readable resources only to substantive targets to avoid edge blow-up."""
            resource_nodes = {nid for nid, label in nodes.items() if self._is_resource_label(label)}
            allowed_targets = {"concept", "definition", "theorem", "pset", "exam"}
            augmented = set(frame)
            step_nodes = {n for u, v in frame for n in (u, v)}
            for resource in resource_nodes & step_nodes:
                for target in step_nodes:
                    if resource == target:
                        continue
                    if node_type_map.get(target, "unknown") not in allowed_targets:
                        continue
                    if (resource, target) not in augmented:
                        augmented.add((resource, target))
                    if (target, resource) not in augmented:
                        augmented.add((target, resource))
            return augmented
    @staticmethod
    def _is_resource_label(label: str) -> bool:
        lower = (label or "").lower()
        if any(ext in lower for ext in (".pdf", "_pdf", ".ipynb", ".jl", ".tex")):
            return True
        if "lecture notes" in lower or "notes" in lower or "resource::" in label:
            return True
        return False

    def _infer_type(self, label: str) -> str:
        text = (label or "").strip()
        lower = text.lower()

        if any(rx.search(text) for rx in self.stop_re):
            return "media"

        nav_tokens = [
            "contact",
            "browse",
            "help",
            "faq",
            "about",
            "give now",
            "syllabus",
            "calendar",
            "recitation",
            "download",
            "transcript",
            "video",
            "problem set",
        ]
        if any(tok in lower for tok in nav_tokens):
            return "nav"

        # Explicit media detection
        if any(s in lower for s in (".mp4", "_mp4")):
            return "media"

        # Treat PDF-labeled lecture resources as substantive content
        if (".pdf" in lower or "_pdf" in lower) and ("lecture" in lower or lower.startswith("lec") or "lec" in lower):
            return "concept"

        for rule in self.custom_rules:
            if any(term.lower() in lower for term in rule.match):
                return rule.type

        if any(term in lower for term in ["exam", "midterm", "final", "quiz", "test"]):
            return "exam"

        if any(term in lower for term in ["problem set", "pset", "assignment", "homework"]):
            return "pset"

        if any(term in lower for term in ["definition", "def.", "def "]):
            return "definition"

        if any(term in lower for term in ["theorem", "lemma", "proposition", "corollary"]):
            return "theorem"

        if any(term in lower for term in ["prof.", "instructor", "jerison", "strang"]):
            return "person"

        concept_tokens = [
            "derivative",
            "integral",
            "series",
            "limit",
            "taylor",
            "chain rule",
            "hopital",
            "riemann",
            "differential",
            "ode",
            "ftc",
            "improper",
            "partial",
            "gradient",
        ]
                # Readable lecture PDFs count as concepts
        if (".pdf" in lower or "_pdf" in lower) and ("lecture" in lower or lower.startswith("lec") or "notes" in lower):
            return "concept"
        if any(tok in lower for tok in concept_tokens):
            return "concept"

        return "unknown"

    def _keep_edge(self, edge: Edge, nodes: Dict[int, str], node_type: Dict[int, str]) -> bool:
        u, v = edge
        label_u = nodes.get(u, "")
        label_v = nodes.get(v, "")

        if label_u in self.stop_nodes or label_v in self.stop_nodes:
            return False
        if label_u.lower() in self.stop_nodes_lower or label_v.lower() in self.stop_nodes_lower:
            return False
        if any(rx.search(label_u) for rx in self.stop_re):
            return False
        if any(rx.search(label_v) for rx in self.stop_re):
            return False

        weight = min(self._node_weight(u, node_type), self._node_weight(v, node_type))
        return weight >= self.keep_threshold

    def _node_weight(self, node_id: int, node_type: Dict[int, str]) -> float:
        ntype = node_type.get(node_id, "unknown")
        return float(self.type_weights.get(ntype, self.type_weights.get("unknown", 0.5)))

    def _cap_step(self, edges: List[Edge]) -> Frame:
        if not edges:
            return set()

        indexed_edges = list(enumerate(edges))
        indexed_edges.sort(key=lambda item: -item[0])

        deg_counts: Dict[int, int] = {}
        result: List[Edge] = []
        for _, (u, v) in indexed_edges:
            if deg_counts.get(u, 0) >= self.topk_per_node:
                continue
            if deg_counts.get(v, 0) >= self.topk_per_node:
                continue
            result.append((u, v))
            deg_counts[u] = deg_counts.get(u, 0) + 1
            deg_counts[v] = deg_counts.get(v, 0) + 1
        return set(result)



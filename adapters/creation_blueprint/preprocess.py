from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Iterable, Set, Tuple

from adapters.base import Frame, ProcessedStream, RawStream
from core.vocabulary import get_adapter_vocab


@dataclass
class CreationBlueprintPreprocessorConfig:
    max_degree: int = 120
    requirement_keywords: Tuple[str, ...] = ("requirement", "must", "shall", "need", "user story")
    component_keywords: Tuple[str, ...] = ("component", "module", "service", "subsystem", "interface", "api")
    process_keywords: Tuple[str, ...] = ("process", "workflow", "step", "stage", "pipeline")
    risk_keywords: Tuple[str, ...] = ("risk", "hazard", "issue", "failure", "concern")
    test_keywords: Tuple[str, ...] = ("test", "validation", "verification", "scenario", "case")
    importance_weights: Dict[str, float] = field(
        default_factory=lambda: {
            "requirement": 1.0,
            "component": 0.8,
            "risk": 0.9,
            "test": 0.7,
            "process": 0.5,
        }
    )


class CreationBlueprintPreprocessor:
    def __init__(self, cfg: CreationBlueprintPreprocessorConfig | None = None):
        self.cfg = cfg or CreationBlueprintPreprocessorConfig()
        vocab = get_adapter_vocab("creation_blueprint")
        if vocab:
            self.cfg.requirement_keywords += tuple(
                marker.lower()
                for marker in vocab.node_markers
                if "requirement" in marker.lower() or "user story" in marker.lower()
            )
            self.cfg.component_keywords += tuple(
                marker.lower()
                for marker in vocab.node_markers
                if any(key in marker.lower() for key in ("component", "module", "interface", "api"))
            )
            self.cfg.risk_keywords += tuple(
                marker.lower() for marker in vocab.node_markers if "risk" in marker.lower()
            )

    @staticmethod
    def _normalize(text: str) -> str:
        return text.strip().lower()

    def _classify_label(self, label: str) -> Set[str]:
        text = self._normalize(label)
        tags: Set[str] = set()
        for key in self.cfg.requirement_keywords:
            if key and key in text:
                tags.add("requirement")
                break
        for key in self.cfg.component_keywords:
            if key and key in text:
                tags.add("component")
                break
        for key in self.cfg.test_keywords:
            if key and key in text:
                tags.add("test")
                break
        for key in self.cfg.risk_keywords:
            if key and key in text:
                tags.add("risk")
                break
        for key in self.cfg.process_keywords:
            if key and key in text:
                tags.add("process")
                break
        if "constraint" in text or "assumption" in text:
            tags.add("constraint")
        return tags

    def _filter_nodes(self, raw: RawStream) -> Tuple[Dict[int, Dict[str, object]], Dict[int, Set[str]]]:
        nodes: Dict[int, Dict[str, object]] = {}
        node_tags: Dict[int, Set[str]] = {}
        for node_id, row in raw.nodes.items():
            label = str(row.get("label") or row.get("raw_type") or node_id)
            tags = self._classify_label(label)
            data = dict(row)
            data.setdefault("label", label)
            nodes[node_id] = data
            node_tags[node_id] = tags
        return nodes, node_tags

    def _cap_degree(self, edges: Frame) -> Frame:
        if self.cfg.max_degree <= 0 or not edges:
            return edges
        degree = defaultdict(int)
        pruned: Set[Tuple[int, int]] = set()
        for u, v in sorted(edges):
            if degree[u] >= self.cfg.max_degree or degree[v] >= self.cfg.max_degree:
                continue
            degree[u] += 1
            degree[v] += 1
            pruned.add((u, v))
        return pruned

    def _summarize_step(
        self,
        step: int,
        edges: Frame,
        node_tags: Dict[int, Set[str]],
        labels: Dict[int, Dict[str, object]],
    ) -> Dict[str, object]:
        if not edges:
            return {
                "quality": 0.0,
                "ted": 0.0,
                "stability": 1.0,
                "top_nodes": [],
                "commentary": "No blueprint updates in this window.",
            }

        step_nodes: Set[int] = {n for edge in edges for n in edge}
        weight_map = self.cfg.importance_weights
        requirement_nodes = {n for n in step_nodes if "requirement" in node_tags.get(n, set())}
        component_nodes = {n for n in step_nodes if "component" in node_tags.get(n, set())}
        test_nodes = {n for n in step_nodes if "test" in node_tags.get(n, set())}
        risk_nodes = {n for n in step_nodes if "risk" in node_tags.get(n, set())}

        linked_requirements = set()
        mitigated_risks = set()
        for u, v in edges:
            u_tags = node_tags.get(u, set())
            v_tags = node_tags.get(v, set())
            if "requirement" in u_tags and (v in component_nodes or v in test_nodes):
                linked_requirements.add(u)
            if "requirement" in v_tags and (u in component_nodes or u in test_nodes):
                linked_requirements.add(v)
            if "risk" in u_tags and (v in test_nodes or v in component_nodes):
                mitigated_risks.add(u)
            if "risk" in v_tags and (u in test_nodes or u in component_nodes):
                mitigated_risks.add(v)

        requirement_total = max(1, len(requirement_nodes))
        coverage = len(linked_requirements) / requirement_total
        risk_total = max(1, len(risk_nodes))
        risk_coverage = len(mitigated_risks) / risk_total if risk_nodes else 1.0

        quality = min(1.0, 0.7 * coverage + 0.3 * risk_coverage)
        ted = round(max(0.0, 1.0 - quality), 3)
        stability = round(min(1.0, quality + 0.2), 3)

        node_scores = []
        for node_id in step_nodes:
            tags = node_tags.get(node_id, set())
            score = sum(weight_map.get(tag, 0.4) for tag in tags)
            if "requirement" in tags and node_id not in linked_requirements:
                score -= 0.3  # penalize unlinked requirements
            if "risk" in tags and node_id not in mitigated_risks:
                score -= 0.2
            node_scores.append((score, node_id))

        node_scores.sort(
            key=lambda pair: (
                -pair[0],
                labels.get(pair[1], {}).get("label", ""),
            )
        )
        top_nodes = [
            {
                "id": node_id,
                "label": labels.get(node_id, {}).get("label", str(node_id)),
                "tags": sorted(node_tags.get(node_id, set())),
                "score": round(score, 3),
            }
            for score, node_id in node_scores[:8]
        ]

        if coverage < 0.6:
            commentary = "Many requirements are unlinked-add design/test coverage."
        elif risk_nodes and risk_coverage < 0.5:
            commentary = "Risks lack mitigations; ensure tests or controls exist."
        else:
            commentary = "Blueprint coverage looks balanced."

        return {
            "quality": round(quality, 3),
            "ted": ted,
            "stability": stability,
            "top_nodes": top_nodes,
            "commentary": commentary,
            "coverage": round(coverage, 3),
            "risk_coverage": round(risk_coverage, 3),
            "counts": {
                "requirements": len(requirement_nodes),
                "components": len(component_nodes),
                "tests": len(test_nodes),
                "risks": len(risk_nodes),
            },
        }

    def process(self, raw: RawStream) -> ProcessedStream:
        nodes, node_tags = self._filter_nodes(raw)

        obs_steps: Dict[int, Frame] = {}
        for step, edges in raw.obs_steps.items():
            kept = {(u, v) for (u, v) in edges if u in nodes and v in nodes and u != v}
            obs_steps[step] = self._cap_degree(kept)

        true_steps: Dict[int, Frame] = {}
        for step, edges in raw.true_steps.items():
            kept = {(u, v) for (u, v) in edges if u in nodes and v in nodes and u != v}
            true_steps[step] = self._cap_degree(kept)

        step_features: Dict[int, Dict[str, object]] = {}
        for step, edges in obs_steps.items():
            step_features[step] = self._summarize_step(step, edges, node_tags, nodes)

        meta = dict(raw.meta)
        meta.setdefault("adapter", "creation_blueprint")
        meta["filtered_nodes"] = len(nodes)

        return ProcessedStream(
            nodes=nodes,
            obs_steps=obs_steps,
            true_steps=true_steps,
            meta=meta,
            step_features=step_features,
            node_tags=node_tags,
        )

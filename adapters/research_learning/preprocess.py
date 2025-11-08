from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Set, Tuple

from adapters.base import Frame, ProcessedStream, RawStream
from core.vocabulary import get_adapter_vocab


@dataclass
class ResearchLearningPreprocessorConfig:
    noise_events: Tuple[str, ...] = ("heartbeat", "auto_save", "keep_alive")
    recency_decay_days: int = 14
    max_degree: int = 80
    assessment_keywords: Tuple[str, ...] = ("quiz", "assignment", "exam", "test", "problem", "exercise")
    resource_keywords: Tuple[str, ...] = ("concept", "note", "lecture", "reading", "summary", "video")
    support_keywords: Tuple[str, ...] = ("forum", "discussion", "hint", "help", "feedback")
    intensity_norm: float = 40.0
    weighting: Dict[str, float] = field(
        default_factory=lambda: {
            "resource": 0.4,
            "assessment": 0.5,
            "support": 0.2,
        }
    )


class ResearchLearningPreprocessor:
    def __init__(self, cfg: ResearchLearningPreprocessorConfig | None = None):
        self.cfg = cfg or ResearchLearningPreprocessorConfig()
        vocab = get_adapter_vocab("research_learning")
        if vocab:
            self.cfg.assessment_keywords += tuple(
                marker.lower()
                for marker in vocab.node_markers
                if any(key in marker.lower() for key in ("quiz", "test", "exam", "problem"))
            )
            self.cfg.resource_keywords += tuple(
                marker.lower()
                for marker in vocab.node_markers
                if any(key in marker.lower() for key in ("concept", "definition", "summary", "example"))
            )

    # ------------------------------------------------------------------ public

    def process(self, raw: RawStream) -> ProcessedStream:
        mode = (raw.meta or {}).get("mode", "activity")
        if mode == "corpus":
            return self._process_corpus(raw)
        return self._process_activity(raw)

    # ------------------------------------------------------------------ activity mode

    def _process_activity(self, raw: RawStream) -> ProcessedStream:
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
            step_features[step] = self._summarize_activity_step(step, edges, node_tags, nodes)

        meta = dict(raw.meta)
        meta.setdefault("adapter", "research_learning")
        meta["filtered_nodes"] = len(nodes)

        return ProcessedStream(
            nodes=nodes,
            obs_steps=obs_steps,
            true_steps=true_steps,
            meta=meta,
            step_features=step_features,
            node_tags=node_tags,
        )

    def _filter_nodes(self, raw: RawStream) -> Tuple[Dict[int, Dict[str, object]], Dict[int, Set[str]]]:
        noise = {self._normalize(ev) for ev in self.cfg.noise_events}
        nodes: Dict[int, Dict[str, object]] = {}
        node_tags: Dict[int, Set[str]] = {}
        for node_id, row in raw.nodes.items():
            label = str(row.get("label") or row.get("resource_label") or row.get("resource_id") or "")
            norm = self._normalize(label)
            if norm in noise:
                continue
            tags = self._classify_label(norm)
            node_entry = dict(row)
            node_entry.setdefault("label", label)
            nodes[node_id] = node_entry
            node_tags[node_id] = tags
        return nodes, node_tags

    def _classify_label(self, label: str) -> Set[str]:
        text = self._normalize(label)
        tags: Set[str] = set()
        for key in self.cfg.assessment_keywords:
            if key and key in text:
                tags.add("assessment")
                break
        for key in self.cfg.resource_keywords:
            if key and key in text:
                tags.add("resource")
                break
        for key in self.cfg.support_keywords:
            if key and key in text:
                tags.add("support")
                break
        if "question" in text or ("why" in text and "assessment" not in tags):
            tags.add("question")
        return tags

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

    def _summarize_activity_step(
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
                "commentary": "No learning activity recorded.",
            }

        step_nodes: Set[int] = {n for edge in edges for n in edge}
        counts = Counter()
        node_scores = []

        for node_id in step_nodes:
            tags = node_tags.get(node_id, set())
            for tag in tags:
                counts[tag] += 1
            score = sum(self.cfg.weighting.get(tag, 0.1) for tag in tags)
            node_scores.append((score, node_id))

        events = len(edges)
        unique_nodes = max(1, len(step_nodes))
        resource_nodes = counts.get("resource", 0)
        assessment_nodes = counts.get("assessment", 0)
        support_nodes = counts.get("support", 0)

        intensity = min(1.0, (events + resource_nodes + assessment_nodes) / (self.cfg.intensity_norm or 40.0))
        consistency = min(1.0, resource_nodes / unique_nodes)
        mastery = min(1.0, (0.6 * assessment_nodes + 0.4 * resource_nodes) / unique_nodes)
        dropout_risk = max(0.0, 1.0 - (0.6 * intensity + 0.4 * consistency))

        quality = min(1.0, 0.5 * mastery + 0.5 * consistency)
        ted = round(dropout_risk, 3)
        stability = round(max(0.0, 1.0 - dropout_risk), 3)

        node_scores.sort(key=lambda pair: (-pair[0], labels.get(pair[1], {}).get("label", "")))
        top_nodes = [
            {
                "id": node_id,
                "label": labels.get(node_id, {}).get("label") or str(node_id),
                "tags": sorted(node_tags.get(node_id, set())),
                "score": round(score, 3),
            }
            for score, node_id in node_scores[:8]
        ]

        if dropout_risk >= 0.6:
            commentary = "Engagement dropping; intervene with targeted prompts or reminders."
        elif mastery >= 0.7:
            commentary = "Learner is consolidating concepts effectively."
        else:
            commentary = "Steady progress; continue monitoring."

        return {
            "quality": round(quality, 3),
            "ted": ted,
            "stability": stability,
            "top_nodes": top_nodes,
            "commentary": commentary,
            "counts": {
                "resource": resource_nodes,
                "assessment": assessment_nodes,
                "support": support_nodes,
                "events": events,
            },
            "intensity": round(intensity, 3),
            "mastery": round(mastery, 3),
            "dropout_risk": round(dropout_risk, 3),
        }

    # ------------------------------------------------------------------ corpus mode

    def _process_corpus(self, raw: RawStream) -> ProcessedStream:
        nodes = {nid: dict(data) for nid, data in raw.nodes.items()}
        node_tags: Dict[int, Set[str]] = {}
        for node_id, data in nodes.items():
            raw_type = str(data.get("raw_type", "")).lower()
            tags: Set[str] = set()
            if raw_type.startswith("doc:"):
                tags.add("doc")
                tags.add(raw_type.split(":", 1)[-1])
            elif raw_type == "section":
                tags.add("section")
            else:
                tags.add("other")
            node_tags[node_id] = tags

        obs_steps: Dict[int, Frame] = {}
        for step, edges in raw.obs_steps.items():
            obs_steps[step] = set(edges)

        true_steps: Dict[int, Frame] = {}
        for step, edges in raw.true_steps.items():
            true_steps[step] = set(edges)

        counts = {
            "doc": sum(1 for n in nodes if "doc" in node_tags.get(n, set())),
            "section": sum(1 for n in nodes if "section" in node_tags.get(n, set())),
        }
        quality = 1.0 if counts["doc"] else 0.0
        commentary = "Corpus graph connectivity looks healthy." if quality else "Corpus is sparse; add more doc links."

        step_features: Dict[int, Dict[str, object]] = {}
        for step in obs_steps or {0}:
            step_features[step] = {
                "quality": quality,
                "ted": 0.0,
                "stability": quality,
                "top_nodes": _top_nodes_for_corpus(nodes, node_tags, limit=8),
                "commentary": commentary,
                "counts": counts,
            }

        meta = dict(raw.meta)
        meta.setdefault("adapter", "research_learning")
        meta["filtered_nodes"] = len(nodes)

        return ProcessedStream(
            nodes=nodes,
            obs_steps=obs_steps,
            true_steps=true_steps,
            meta=meta,
            step_features=step_features,
            node_tags=node_tags,
        )

    # ------------------------------------------------------------------ helpers

    @staticmethod
    def _normalize(text: str) -> str:
        return text.strip().lower()


def _top_nodes_for_corpus(
    nodes: Dict[int, Dict[str, object]],
    node_tags: Dict[int, Set[str]],
    limit: int,
) -> List[Dict[str, object]]:
    scored = []
    for node_id, data in nodes.items():
        tags = node_tags.get(node_id, set())
        score = 1.0 if "doc" in tags else 0.8 if "section" in tags else 0.2
        scored.append((score, node_id, data))
    scored.sort(key=lambda entry: (-entry[0], str(entry[2].get("label", ""))))
    summary = []
    for score, node_id, data in scored[:limit]:
        summary.append(
            {
                "id": node_id,
                "label": data.get("label", ""),
                "tags": sorted(node_tags.get(node_id, set())),
                "score": round(score, 3),
            }
        )
    return summary

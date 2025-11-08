from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Set, Tuple

from adapters.base import Frame, ProcessedStream, RawStream
from core.vocabulary import get_adapter_vocab


@dataclass
class ConversationBrainstormPreprocessorConfig:
    stop_terms: Tuple[str, ...] = ("um", "uh", "like", "you know")
    min_turn_tokens: int = 3
    max_degree: int = 120
    build_synonyms: Tuple[str, ...] = ("build on", "following up", "adding to")
    critique_synonyms: Tuple[str, ...] = ("concern", "risk", "problem", "issue", "challenge")
    decision_synonyms: Tuple[str, ...] = ("decide", "decision", "agreement", "vote")
    weighting: Dict[str, Dict[str, float]] = field(
        default_factory=lambda: {
            "idea": 1.0,
            "build": 0.8,
            "decision": 0.6,
            "summary": 0.4,
            "critique": -0.4,
            "question": -0.2,
        }
    )


class ConversationBrainstormPreprocessor:
    tag_keywords: Dict[str, Iterable[str]] = {
        "idea": (
            "idea",
            "suggestion",
            "proposal",
            "option",
            "variant",
            "angle",
            "theme",
            "direction",
        ),
        "critique": ("critique", "counterpoint", "objection", "pushback", "challenge"),
        "question": ("question", "clarify", "clarification", "why", "how", "who", "what"),
        "summary": ("summary", "takeaway", "recap", "overview"),
        "decision": ("decision", "priority", "next step", "action item", "follow-up", "task"),
    }

    def __init__(self, cfg: ConversationBrainstormPreprocessorConfig | None = None):
        self.cfg = cfg or ConversationBrainstormPreprocessorConfig()
        vocab = get_adapter_vocab("conversation_brainstorm")
        self.vocab = vocab
        if vocab:
            expanded = set(self.tag_keywords.get("idea", ()))
            for marker in vocab.node_markers:
                marker_lower = marker.lower()
                if "idea" in marker_lower or "suggest" in marker_lower or "proposal" in marker_lower:
                    expanded.add(marker_lower)
            self.tag_keywords["idea"] = tuple(sorted(expanded))
        self._build_terms = tuple(term.lower() for term in self.cfg.build_synonyms)
        self._critique_terms = tuple(term.lower() for term in self.cfg.critique_synonyms)
        self._decision_terms = tuple(term.lower() for term in self.cfg.decision_synonyms)

    @staticmethod
    def _normalize(text: str) -> str:
        return text.strip().lower()

    def _token_count(self, text: str) -> int:
        tokens = [t for t in re.split(r"\W+", text) if t]
        return len(tokens)

    def _classify_label(self, label: str) -> Set[str]:
        text = self._normalize(label)
        tags: Set[str] = set()

        for tag, keywords in self.tag_keywords.items():
            for keyword in keywords:
                keyword_lower = keyword.lower()
                if keyword_lower and keyword_lower in text:
                    tags.add(tag)
                    break

        if any(term in text for term in self._build_terms):
            tags.add("build")
        if any(term in text for term in self._critique_terms):
            tags.add("critique")
        if any(term in text for term in self._decision_terms):
            tags.add("decision")

        if "question" in tags and "idea" not in tags and "critique" not in tags:
            tags.add("question")
        if "idea" in tags and "build" not in tags and "build" in text:
            tags.add("build")
        return tags

    def _filter_nodes(self, raw: RawStream) -> Tuple[Dict[int, Dict[str, object]], Dict[int, Set[str]]]:
        filtered_nodes: Dict[int, Dict[str, object]] = {}
        node_tags: Dict[int, Set[str]] = {}
        stop_lower = {self._normalize(term) for term in self.cfg.stop_terms}

        for node_id, row in raw.nodes.items():
            text = str(row.get("text") or row.get("label") or "")
            norm = self._normalize(text)
            if norm in stop_lower:
                continue
            if self._token_count(norm) < self.cfg.min_turn_tokens:
                continue
            tags = self._classify_label(norm)
            filtered_nodes[node_id] = dict(row)
            filtered_nodes[node_id]["text"] = text
            node_tags[node_id] = tags
        return filtered_nodes, node_tags

    def _cap_degree(self, edges: Frame) -> Frame:
        if self.cfg.max_degree <= 0 or not edges:
            return edges
        degree: Dict[int, int] = defaultdict(int)
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
        labels: Dict[int, str],
    ) -> Dict[str, object]:
        if not edges:
            return {
                "quality": 0.0,
                "ted": 0.0,
                "stability": 1.0,
                "top_nodes": [],
                "commentary": "No activity captured for this window.",
            }

        step_nodes: Set[int] = {n for edge in edges for n in edge}
        counts = Counter()
        weights = self.cfg.weighting

        node_scores: List[Tuple[float, int]] = []

        for node_id in step_nodes:
            tags = node_tags.get(node_id, set())
            label_row = labels.get(node_id, {})
            text = label_row.get("text") or label_row.get("label") or str(node_id)
            for tag in tags:
                counts[tag] += 1

            score = 0.0
            for tag in tags:
                score += weights.get(tag, 0.1)
            node_scores.append((score, node_id, text))

        total_nodes = max(1, len(step_nodes))
        ideas = counts.get("idea", 0)
        builds = counts.get("build", 0)
        decisions = counts.get("decision", 0)
        critiques = counts.get("critique", 0)
        questions = counts.get("question", 0)

        idea_component = ideas + 0.8 * builds + 0.5 * decisions
        quality = min(1.0, idea_component / total_nodes)

        critique_ratio = critiques / total_nodes
        question_ratio = questions / total_nodes
        ted = max(0.0, min(1.0, 0.7 * critique_ratio + 0.3 * question_ratio))
        stability = max(0.0, min(1.0, 1.0 - ted + 0.2 * (builds / total_nodes if total_nodes else 0.0)))
        build_ratio = builds / max(1, ideas + builds)

        node_scores.sort(key=lambda pair: (-pair[0], pair[2]))
        top_nodes = [
            {
                "id": node_id,
                "label": labels.get(node_id, {}).get("text") or labels.get(node_id, {}).get("label") or str(node_id),
                "tags": sorted(node_tags.get(node_id, set())),
                "score": round(score, 3),
            }
            for score, node_id, _ in node_scores[:8]
        ]

        if quality >= 0.75 and critique_ratio <= 0.2:
            commentary = "Healthy idea flow with balanced collaboration."
        elif ted >= 0.6:
            commentary = "Conversation is trending defensive; surface follow-up or converging moves."
        elif build_ratio < 0.3 and ideas > 0:
            commentary = "Ideas are emerging but could use more building and synthesis."
        else:
            commentary = "Session progressing normally."

        return {
            "quality": round(quality, 3),
            "ted": round(ted, 3),
            "stability": round(stability, 3),
            "top_nodes": top_nodes,
            "commentary": commentary,
            "counts": {
                "idea": ideas,
                "build": builds,
                "decision": decisions,
                "critique": critiques,
                "question": questions,
            },
        }

    def process(self, raw: RawStream) -> ProcessedStream:
        filtered_nodes, node_tags = self._filter_nodes(raw)

        obs_steps: Dict[int, Frame] = {}
        for step, edges in raw.obs_steps.items():
            kept = {(u, v) for (u, v) in edges if u in filtered_nodes and v in filtered_nodes and u != v}
            obs_steps[step] = self._cap_degree(kept)

        true_steps: Dict[int, Frame] = {}
        for step, edges in raw.true_steps.items():
            kept = {(u, v) for (u, v) in edges if u in filtered_nodes and v in filtered_nodes and u != v}
            true_steps[step] = self._cap_degree(kept)

        step_features: Dict[int, Dict[str, object]] = {}
        for step, edges in obs_steps.items():
            step_features[step] = self._summarize_step(step, edges, node_tags, filtered_nodes)

        meta = dict(raw.meta)
        meta.setdefault("adapter", "conversation_brainstorm")
        meta["filtered_nodes"] = len(filtered_nodes)

        return ProcessedStream(
            nodes=filtered_nodes,
            obs_steps=obs_steps,
            true_steps=true_steps,
            meta=meta,
            step_features=step_features,
            node_tags=node_tags,
        )

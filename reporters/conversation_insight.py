from __future__ import annotations

from typing import Dict, List, Optional

from core.registry import register_reporter
from .insight import InsightReporter


@register_reporter("conversation_insight")
class ConversationInsightReporter(InsightReporter):
    def __init__(self, domain: str = "conversation", path: str = "reports/conversation_insight.json"):
        super().__init__(domain=domain, path=path)
        self._adjacency_ratios: List[float] = []
        self._question_densities: List[float] = []
        self._speaker_counts: List[int] = []
        self._turn_counts: List[int] = []
        self._active_domain = False

    def start(self, meta: dict, config: dict):
        super().start(meta, config)
        self._active_domain = meta.get("domain") == "conversation"

    def record(self, step: int, signals: dict, meta: dict, pred, regret: Optional[float] = None):
        if not self._active_domain:
            return

        reply_edges = int(meta.get("reply_edges") or 0)
        adjacency_edges = int(meta.get("adjacency_edges") or 0)
        question_count = int(meta.get("question_count") or 0)
        turn_count = int(meta.get("turn_count") or 0)
        speaker_count = int(meta.get("speaker_count") or len(meta.get("speakers") or []))

        ratio = round(reply_edges / max(adjacency_edges, 1), 3) if adjacency_edges else 0.0
        density = round(question_count / max(turn_count, 1), 3)

        self._adjacency_ratios.append(ratio)
        self._question_densities.append(density)
        self._speaker_counts.append(speaker_count)
        self._turn_counts.append(turn_count)

        super().record(step, signals, meta, pred, regret)

    def _extend_summary(self):
        if not self._adjacency_ratios:
            return
        highlights = {
            "avg_adjacency_ratio": round(sum(self._adjacency_ratios) / len(self._adjacency_ratios), 3),
            "avg_question_density": round(sum(self._question_densities) / len(self._question_densities), 3),
            "avg_speaker_count": round(sum(self._speaker_counts) / len(self._speaker_counts), 3),
            "avg_turns_per_step": round(sum(self._turn_counts) / len(self._turn_counts), 3),
        }
        self.summary["conversation_highlights"] = highlights

    def finish(self):
        if not self._active_domain or not self._adjacency_ratios:
            return
        super().finish()

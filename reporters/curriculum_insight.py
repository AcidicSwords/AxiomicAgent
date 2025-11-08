from __future__ import annotations

from typing import Dict, List

from core.registry import register_reporter
from .insight import InsightReporter


@register_reporter("curriculum_insight")
class CurriculumInsightReporter(InsightReporter):
    def __init__(self, domain: str = "curriculum", path: str = "reports/curriculum_insight.json"):
        super().__init__(domain=domain, path=path)

    def _extend_summary(self):
        aggregates = self.summary.get("aggregates", {})
        steps = self.summary.get("steps", [])
        continuity_vals = [step.get("continuity") for step in steps if isinstance(step.get("continuity"), (int, float))]
        avg_continuity = round(sum(continuity_vals) / len(continuity_vals), 3) if continuity_vals else None
        phase_counts = aggregates.get("step_types") or {}
        highlight = {
            "phase_counts": phase_counts,
            "avg_continuity": avg_continuity,
            "avg_ted_trusted": aggregates.get("avg_ted_trusted"),
            "dominant_step_type": max(phase_counts, key=phase_counts.get) if phase_counts else None,
        }
        self.summary["curriculum_highlights"] = highlight

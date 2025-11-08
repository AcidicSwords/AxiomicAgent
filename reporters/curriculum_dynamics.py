"""
Curriculum dynamics reporter.

Per-step fields captured:
- q, ted, stability, spread, ted_delta, continuity
- step_type (inferred), next_step_type_pred
- q_mc_std, ted_mc_std, change_score
- top_nodes, commentary

Aggregates:
- avg_q, avg_ted, step_type_distribution, trend slopes
- avg MC stds, most uncertain steps
- phases + guidance block
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.registry import register_reporter


def _safe_float(value, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


@register_reporter("curriculum_dynamics")
class CurriculumDynamicsReporter:
    """
    Reporter tailored for curriculum-style datasets.
    Captures per-step dynamics, robustness estimates, phase boundaries,
    and emits guidance for downstream LLM tools.
    """

    def __init__(self, path: str = "reports/curriculum_dynamics.json", **_: Any):
        self.path = Path(path)
        self.summary: Dict[str, Any] = {
            "run_meta": {},
            "steps": [],
            "dynamics": {},
            "phases": [],
            "uncertainty": {},
            "guidance": {},
        }

    def start(self, meta: Dict[str, Any], config: Dict[str, Any]) -> None:
        self.summary["run_meta"] = {
            "dataset": meta.get("dataset_path"),
            "course_id": meta.get("course_id"),
            "steps": meta.get("steps"),
            "nodes": meta.get("nodes"),
            "policy": config.get("policy"),
        }

    def record(self, step: int, signals: Dict[str, Any], meta: Dict[str, Any], pred, regret: Optional[float] = None) -> None:
        entry = {
            "step": step,
            "step_id": meta.get("step_id", step),
            "q": signals.get("q"),
            "ted": signals.get("ted"),
            "stability": signals.get("s"),
            "spread": signals.get("spread"),
            "ted_delta": signals.get("ted_delta"),
            "continuity": signals.get("continuity"),
            "step_type": signals.get("step_type_inferred") or signals.get("step_type") or meta.get("step_type"),
            "next_step_type_pred": signals.get("next_step_type_pred"),
            "q_mc_std": signals.get("q_mc_std"),
            "ted_mc_std": signals.get("ted_mc_std"),
            "change_score": signals.get("change_score"),
            "top_nodes": meta.get("top_nodes", []),
            "commentary": meta.get("commentary"),
        }
        self.summary["steps"].append(entry)

    def finish(self) -> None:
        steps: List[Dict[str, Any]] = self.summary.get("steps", [])
        if steps:
            avg_q = sum(_safe_float(s.get("q")) for s in steps) / len(steps)
            avg_ted = sum(_safe_float(s.get("ted")) for s in steps) / len(steps)
            step_type_counts = Counter(s.get("step_type") or "unknown" for s in steps)
        else:
            avg_q = avg_ted = 0.0
            step_type_counts = Counter()

        head_summaries: Dict[str, Dict[str, Any]] = self.summary.get("head_summaries", {})
        monte_carlo = head_summaries.get("monte_carlo", {})
        forecast = head_summaries.get("forecast", {})
        regime = head_summaries.get("regime_change", {})

        # Fallback slope computation if forecast head not enabled
        def _fallback_slope(key: str) -> float | None:
            if not steps:
                return None
            xs = list(range(len(steps)))
            ys = [_safe_float(s.get(key), None) for s in steps]
            if any(v is None for v in ys):
                # filter out None rows
                pairs = [(i, v) for i, v in zip(xs, ys) if isinstance(v, (int, float))]
                if len(pairs) < 2:
                    return None
                xs, ys = zip(*pairs)
            n = len(xs)
            if n < 2:
                return 0.0
            mean_x = sum(xs) / n
            mean_y = sum(ys) / n
            num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
            den = sum((x - mean_x) ** 2 for x in xs) or 1.0
            return num / den

        q_slope = forecast.get("q_trend_slope")
        if q_slope is None:
            q_slope = _fallback_slope("q")
        ted_slope = forecast.get("ted_trend_slope")
        if ted_slope is None:
            ted_slope = _fallback_slope("ted")

        self.summary["dynamics"] = {
            "avg_q": round(avg_q, 3),
            "avg_ted": round(avg_ted, 3),
            "step_type_distribution": dict(step_type_counts),
            "q_trend_slope": q_slope,
            "ted_trend_slope": ted_slope,
        }

        # Fallback uncertainty averages from per-step values
        avg_q_mc = monte_carlo.get("avg_q_mc_std")
        avg_ted_mc = monte_carlo.get("avg_ted_mc_std")
        if avg_q_mc is None and steps:
            vals = [s.get("q_mc_std") for s in steps if isinstance(s.get("q_mc_std"), (int, float))]
            avg_q_mc = (sum(vals) / len(vals)) if vals else None
        if avg_ted_mc is None and steps:
            vals = [s.get("ted_mc_std") for s in steps if isinstance(s.get("ted_mc_std"), (int, float))]
            avg_ted_mc = (sum(vals) / len(vals)) if vals else None

        self.summary["uncertainty"] = {
            "avg_q_mc_std": avg_q_mc,
            "avg_ted_mc_std": avg_ted_mc,
            "most_uncertain_steps": self._top_uncertain_steps(steps, key="q_mc_std"),
        }

        self.summary["phases"] = self._build_phases(regime.get("change_points", []), len(steps))
        self.summary["guidance"] = self._build_guidance(forecast, self.summary["phases"])

        out = dict(self.summary)
        out.pop("head_summaries", None)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(out, indent=2))

    # ------------------------------------------------------------------

    @staticmethod
    def _top_uncertain_steps(steps: List[Dict[str, Any]], key: str, top_n: int = 5) -> List[Dict[str, Any]]:
        ranked = sorted(
            (
                {"step": s.get("step"), key: s.get(key)}
                for s in steps
                if isinstance(s.get(key), (int, float))
            ),
            key=lambda entry: entry[key],
            reverse=True,
        )
        return ranked[:top_n]

    @staticmethod
    def _build_phases(change_points: List[int], total_steps: int) -> List[Dict[str, Any]]:
        if not change_points or total_steps <= 0:
            return []
        points = sorted(set(cp for cp in change_points if 0 <= cp < total_steps))
        phases = []
        start = 0
        for idx, cp in enumerate(points):
            phases.append({"phase": idx + 1, "start": start, "end": cp})
            start = cp + 1
        if start < total_steps:
            phases.append({"phase": len(points) + 1, "start": start, "end": total_steps - 1})
        return phases

    @staticmethod
    def _build_guidance(forecast_summary: Dict[str, Any], phases: List[Dict[str, Any]]) -> Dict[str, Any]:
        step_types = forecast_summary.get("step_type_sequence") or []
        next_focus = step_types[-1] if step_types else "unknown"
        guidance = {
            "dominant_step_types": Counter(step_types).most_common(3),
            "next_focus_hint": next_focus,
        }
        if phases:
            guidance["phase_count"] = len(phases)
        return guidance

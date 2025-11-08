from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List

from core.heads import SignalHead, StepFrame


class ForecastHead(SignalHead):
    """Simple trend + next-step type predictor."""

    name = "forecast"

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        super().__init__(config)
        cfg = (config or {}).get("forecast", {})
        self.window_size = int(cfg.get("window_size", 3))
        self._history: List[Dict[str, Any]] = []
        self._step_types: List[str] = []

    def init_course(self, course_id: str, meta: Dict[str, Any]) -> None:
        self._history = []
        self._step_types = []

    def per_step(self, frame: StepFrame, base_signals: Dict[str, float]) -> Dict[str, Any]:
        features = {
            "t": frame.t,
            "q": base_signals.get("q", 0.0),
            "ted": base_signals.get("ted", 0.0),
            "concept_fraction": frame.step_features.get("concept_fraction", 0.0),
            "assessment_fraction": frame.step_features.get("assessment_fraction", 0.0),
            "reading_fraction": frame.step_features.get("reading_fraction", 0.0),
        }
        self._history.append(features)

        step_type = frame.step_features.get("step_type")
        if not step_type:
            step_type = self._classify_step(features)
        self._step_types.append(step_type)

        next_type_pred = self._predict_next_type()
        return {
            "step_type_inferred": step_type,
            "next_step_type_pred": next_type_pred,
        }

    def finalize_course(self) -> Dict[str, Any]:
        if not self._history:
            return {}
        q_slope = self._compute_slope([h["t"] for h in self._history], [h["q"] for h in self._history])
        ted_slope = self._compute_slope([h["t"] for h in self._history], [h["ted"] for h in self._history])
        return {
            "q_trend_slope": q_slope,
            "ted_trend_slope": ted_slope,
            "step_type_sequence": list(self._step_types),
        }

    def _predict_next_type(self) -> str:
        window = self._step_types[-self.window_size :]
        filtered = [label for label in window if label not in ("empty", "", None)]
        if not filtered:
            return "unknown"
        counts = Counter(filtered)
        return counts.most_common(1)[0][0]

    @staticmethod
    def _classify_step(features: Dict[str, float]) -> str:
        q = features.get("q", 0.0)
        ted = features.get("ted", 0.0)
        concept = features.get("concept_fraction", 0.0)
        assessment = features.get("assessment_fraction", 0.0)
        reading = features.get("reading_fraction", 0.0)

        if q <= 0.0:
            return "empty"
        if assessment > 0.4 and concept > 0.2:
            return "checkpoint"
        if concept > 0.55 and assessment < 0.25:
            return "concept_dense"
        if reading > 0.45 and assessment < 0.2:
            return "reading_heavy"
        if ted > 0.35:
            return "transition"
        return "mixed"

    @staticmethod
    def _compute_slope(xs: List[float], ys: List[float]) -> float:
        if not xs or not ys or len(xs) != len(ys):
            return 0.0
        n = len(xs)
        mean_x = sum(xs) / n
        mean_y = sum(ys) / n
        numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
        denominator = sum((x - mean_x) ** 2 for x in xs) or 1.0
        return numerator / denominator

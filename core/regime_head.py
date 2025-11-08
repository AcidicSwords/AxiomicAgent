from __future__ import annotations

from typing import Any, Dict, List

from core.heads import SignalHead, StepFrame


class RegimeChangeHead(SignalHead):
    """Simple change-point detection over sliding windows."""

    name = "regime_change"

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        super().__init__(config)
        cfg = (config or {}).get("regime_change", {})
        self.window = int(cfg.get("window", 3))
        self.threshold = float(cfg.get("threshold", 0.25))
        self._history: List[Dict[str, Any]] = []
        self._change_points: List[int] = []

    def init_course(self, course_id: str, meta: Dict[str, Any]) -> None:
        self._history = []
        self._change_points = []

    def per_step(self, frame: StepFrame, base_signals: Dict[str, float]) -> Dict[str, Any]:
        feature_vector = {
            "t": frame.t,
            "q": base_signals.get("q", 0.0),
            "ted": base_signals.get("ted", 0.0),
            "concept_fraction": frame.step_features.get("concept_fraction", 0.0),
            "assessment_fraction": frame.step_features.get("assessment_fraction", 0.0),
            "reading_fraction": frame.step_features.get("reading_fraction", 0.0),
        }
        self._history.append(feature_vector)

        change_score = 0.0
        k = self.window
        if len(self._history) >= 2 * k + 1:
            center_idx = len(self._history) - 1 - k
            prev_window = self._history[center_idx - k : center_idx]
            next_window = self._history[center_idx + 1 : center_idx + 1 + k]
            if len(prev_window) == k and len(next_window) == k:
                prev_avg = self._average(prev_window)
                next_avg = self._average(next_window)
                change_score = self._l2_distance(prev_avg, next_avg)
                if change_score >= self.threshold:
                    self._change_points.append(center_idx)

        return {"change_score": change_score}

    def finalize_course(self) -> Dict[str, Any]:
        return {
            "change_points": list(self._change_points),
            "num_change_points": len(self._change_points),
        }

    @staticmethod
    def _average(window: List[Dict[str, float]]) -> Dict[str, float]:
        keys = ["q", "ted", "concept_fraction", "assessment_fraction", "reading_fraction"]
        sums = {key: 0.0 for key in keys}
        for entry in window:
            for key in keys:
                sums[key] += entry.get(key, 0.0)
        return {key: sums[key] / len(window) for key in keys}

    @staticmethod
    def _l2_distance(a: Dict[str, float], b: Dict[str, float]) -> float:
        keys = ["q", "ted", "concept_fraction", "assessment_fraction", "reading_fraction"]
        return sum((a.get(key, 0.0) - b.get(key, 0.0)) ** 2 for key in keys) ** 0.5

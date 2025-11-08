from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from core.registry import register_reporter


@dataclass
class StepEntry:
    step: int
    mean_q: Optional[float]
    mean_ted: Optional[float]
    mean_s: Optional[float]
    delta_ted: Optional[float]
    top_nodes: List[dict]
    commentary: str
    counts: Dict[str, int] = field(default_factory=dict)
    spread: Optional[float] = None
    locality_nodes: Optional[List[int]] = None
    step_type: Optional[str] = None
    edge_count: Optional[int] = None
    fractions: Dict[str, float] = field(default_factory=dict)


@register_reporter("insight")
class InsightReporter:
    def __init__(self, domain: str = "generic", path: str = "reports/insight_summary.json"):
        self.domain = domain
        self.path = Path(path)
        self.summary = {
            "domain": domain,
            "run_meta": {},
            "steps": [],
            "aggregates": {},
            "recommendations": [],
        }
        self._prev_ted: Optional[float] = None
        self._series_q: List[float] = []
        self._series_ted: List[float] = []
        self._series_s: List[float] = []
        self._series_spread: List[float] = []
        self._type_counts: Dict[str, int] = {}

    def start(self, meta: dict, config: dict):
        self.summary["run_meta"] = {
            "dataset": meta.get("dataset_path"),
            "hash": meta.get("hash"),
            "steps": meta.get("steps"),
            "nodes": meta.get("nodes"),
            "adapter": meta.get("adapter"),
            "policy": config.get("policy"),
            "capacity": config.get("capacity"),
        }

    def record(self, step: int, signals: dict, meta: dict, pred, regret: Optional[float] = None):
        q = signals.get("q")
        ted = signals.get("ted")
        stability = signals.get("s")
        delta_ted = signals.get("ted_delta")
        spread = signals.get("spread")
        locality_nodes = signals.get("locality_nodes")

        if isinstance(q, (int, float)):
            self._series_q.append(float(q))
        if isinstance(ted, (int, float)):
            self._series_ted.append(float(ted))
        if isinstance(stability, (int, float)):
            self._series_s.append(float(stability))
        if isinstance(spread, (int, float)):
            self._series_spread.append(float(spread))

        fractions = self._extract_fraction_map(meta)
        commentary = meta.get("commentary", "Run progressing normally.")
        step_type = meta.get("step_type")

        if self.domain == "curriculum":
            step_type, commentary = self._curriculum_commentary(
                base_commentary=commentary,
                fractions=fractions,
                signals=signals,
                meta=meta,
            )

        if step_type:
            self._type_counts[step_type] = self._type_counts.get(step_type, 0) + 1

        entry = StepEntry(
            step=step,
            mean_q=q,
            mean_ted=ted,
            mean_s=stability,
            delta_ted=delta_ted,
            top_nodes=meta.get("top_nodes", []),
            commentary=commentary,
            counts={k: int(v) for k, v in meta.get("counts", {}).items()},
            spread=spread,
            locality_nodes=locality_nodes,
            step_type=step_type,
            edge_count=meta.get("edge_count"),
            fractions=fractions,
        )
        self.summary["steps"].append(entry.__dict__)

    def finish(self):
        aggregates = {
            "avg_q": round(sum(self._series_q) / len(self._series_q), 3) if self._series_q else None,
            "avg_ted": round(sum(self._series_ted) / len(self._series_ted), 3) if self._series_ted else None,
            "avg_stability": round(sum(self._series_s) / len(self._series_s), 3) if self._series_s else None,
            "avg_spread": round(sum(self._series_spread) / len(self._series_spread), 3) if self._series_spread else None,
            "steps": len(self.summary["steps"]),
        }
        if self._type_counts:
            aggregates["step_types"] = dict(sorted(self._type_counts.items()))
        self.summary["aggregates"] = aggregates

        recs: List[str] = []
        if aggregates.get("avg_ted") and aggregates["avg_ted"] > 0.6:
            recs.append("High drift detected; schedule a review or escalation.")
        if aggregates.get("avg_q") and aggregates["avg_q"] < 0.4:
            recs.append("Quality is lagging; consider injecting higher-signal context.")
        if not recs:
            recs.append("System performing within expected ranges.")
        self.summary["recommendations"] = recs

        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.summary, indent=2))

    # ------------------------------------------------------------------

    @staticmethod
    def _extract_fraction_map(meta: dict) -> Dict[str, float]:
        fractions = {}
        for key in ("concept_fraction", "assessment_fraction", "reading_fraction", "meta_fraction"):
            value = meta.get(key)
            if isinstance(value, (int, float)):
                fractions[key] = float(value)
            else:
                fractions[key] = 0.0
        return fractions

    def _curriculum_commentary(
        self,
        *,
        base_commentary: str,
        fractions: Dict[str, float],
        signals: dict,
        meta: dict,
    ) -> tuple[Optional[str], str]:
        q = self._coerce_float(signals.get("q"), meta.get("quality"))
        nav_noise = self._coerce_float(meta.get("nav_noise"), fractions.get("meta_fraction", 0.0))
        edge_count = int(meta.get("edge_count") or 0)
        step_type = meta.get("step_type")

        if not step_type:
            step_type = self._classify_curriculum_step(
                q=q,
                fractions=fractions,
                meta_fraction=fractions.get("meta_fraction", 0.0),
                nav_noise=nav_noise,
                edge_count=edge_count,
            )

        commentary = base_commentary
        if step_type == "empty":
            commentary = "No curriculum updates recorded."
        elif step_type == "checkpoint":
            commentary = (
                "Major checkpoint week; assessments closely follow current concepts "
                f"(concept share={fractions['concept_fraction']:.2f}, "
                f"assessments={fractions['assessment_fraction']:.2f})."
            )
        elif step_type == "concept_dense":
            commentary = (
                "Concept-dense segment; ideal for exploration and teaching "
                f"(concept share={fractions['concept_fraction']:.2f})."
            )
        elif step_type == "reading_heavy":
            commentary = (
                "Reading-heavy window; emphasize synthesis and discussion "
                f"(reading share={fractions['reading_fraction']:.2f})."
            )
        elif step_type == "transition":
            commentary = (
                "Transition/structural week; navigation/meta nodes dominate "
                f"(noise={nav_noise:.2f})."
            )

        return step_type, commentary

    @staticmethod
    def _coerce_float(primary, fallback) -> float:
        for value in (primary, fallback, 0.0):
            try:
                return float(value)
            except (TypeError, ValueError):
                continue
        return 0.0

    @staticmethod
    def _classify_curriculum_step(
        *,
        q: float,
        fractions: Dict[str, float],
        meta_fraction: float,
        nav_noise: float,
        edge_count: int,
    ) -> str:
        if edge_count <= 0 or q <= 0.01:
            return "empty"
        concept = fractions.get("concept_fraction", 0.0)
        assessment = fractions.get("assessment_fraction", 0.0)
        reading = fractions.get("reading_fraction", 0.0)
        if assessment >= 0.35 and concept >= 0.2:
            return "checkpoint"
        if concept >= 0.55 and assessment <= 0.25:
            return "concept_dense"
        if reading >= 0.45 and assessment <= 0.2:
            return "reading_heavy"
        if meta_fraction >= 0.3 or nav_noise >= 0.45:
            return "transition"
        return "mixed"

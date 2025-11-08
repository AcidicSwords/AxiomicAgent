from __future__ import annotations

import json
from pathlib import Path

from reporters.curriculum_dynamics import CurriculumDynamicsReporter


def test_curriculum_dynamics_reporter_outputs_sections(tmp_path: Path):
    reporter = CurriculumDynamicsReporter(path=str(tmp_path / "report.json"))
    reporter.start({"course_id": "demo", "steps": 2, "nodes": 5}, {"policy": "Identity"})

    signals_step0 = {
        "q": 0.8,
        "ted": 0.1,
        "s": 0.9,
        "spread": 0.0,
        "ted_delta": 0.0,
        "step_type_inferred": "concept_dense",
        "next_step_type_pred": "concept_dense",
        "q_mc_std": 0.01,
        "ted_mc_std": 0.02,
        "change_score": 0.0,
    }
    meta = {"step_id": 0, "top_nodes": [], "commentary": "Good coverage"}
    reporter.record(0, signals_step0, meta, pred=None)

    signals_step1 = dict(signals_step0)
    signals_step1["q"] = 0.6
    signals_step1["step_type_inferred"] = "checkpoint"
    signals_step1["change_score"] = 0.5
    reporter.record(1, signals_step1, meta, pred=None)

    reporter.summary["head_summaries"] = {
        "monte_carlo": {"avg_q_mc_std": 0.02, "avg_ted_mc_std": 0.03},
        "forecast": {"q_trend_slope": -0.1, "ted_trend_slope": 0.05, "step_type_sequence": ["concept_dense", "checkpoint"]},
        "regime_change": {"change_points": [1], "num_change_points": 1},
    }

    reporter.finish()

    data = json.loads((tmp_path / "report.json").read_text())
    assert "dynamics" in data
    assert "uncertainty" in data
    assert data["guidance"]["dominant_step_types"]

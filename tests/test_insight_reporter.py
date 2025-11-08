from __future__ import annotations

import json

from reporters.insight import InsightReporter


def test_curriculum_reporter_classifies_step(tmp_path):
    reporter = InsightReporter(domain="curriculum", path=str(tmp_path / "insight.json"))
    reporter.start(
        meta={"dataset_path": "demo", "hash": "abc", "steps": 1, "nodes": 3, "adapter": "curriculum_stream"},
        config={"policy": "IdentityPolicy", "capacity": 10},
    )

    signals = {"q": 0.82, "ted": 0.12, "s": 0.91, "ted_delta": 0.0, "spread": None, "locality_nodes": None}
    step_meta = {
        "step_id": 0,
        "top_nodes": [],
        "commentary": "placeholder",
        "counts": {},
        "concept_fraction": 0.5,
        "assessment_fraction": 0.4,
        "reading_fraction": 0.1,
        "meta_fraction": 0.0,
        "edge_count": 6,
    }

    reporter.record(step=0, signals=signals, meta=step_meta, pred=None)
    reporter.finish()

    payload = json.loads((tmp_path / "insight.json").read_text())
    step_entry = payload["steps"][0]
    assert step_entry["step_type"] == "checkpoint"
    assert "checkpoint" in step_entry["commentary"].lower()

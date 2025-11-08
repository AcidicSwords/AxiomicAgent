from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.engine import Engine
from core.policy import IdentityPolicy
from core.signals import DefaultSignalComputer


ROOT = Path(__file__).resolve().parents[1]

FIXTURES = [
    (
        "curriculum_test",
        "curriculum_stream",
        "datasets/curriculum_test.zip",
        "tests/fixtures/insights/golden/curriculum.identity.json",
    ),
]


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


@pytest.mark.parametrize("domain, adapter, dataset, golden_path", FIXTURES)
def test_engine_matches_golden(tmp_path, domain, adapter, dataset, golden_path):
    golden = load_json(ROOT / golden_path)
    out_path = tmp_path / f"{domain}_insight.json"

    engine = Engine(
        adapter=adapter,
        dataset_path=ROOT / dataset,
        reporter="insight",
        reporter_kwargs={"domain": domain, "path": str(out_path)},
        signal_computer=DefaultSignalComputer(),
        policy=IdentityPolicy(),
    )
    engine.run()

    report = load_json(out_path)

    assert report["run_meta"]["policy"] == golden["run_meta"]["policy"]
    assert len(report["steps"]) == len(golden["steps"])

    for key in ("avg_q", "avg_ted", "avg_stability", "avg_spread"):
        assert key in report["aggregates"]
        assert key in golden["aggregates"]
        r_val = report["aggregates"][key]
        g_val = golden["aggregates"][key]
        if r_val is None or g_val is None:
            assert r_val == g_val
        else:
            assert abs(r_val - g_val) < 0.01

    for step in (report["steps"][0], report["steps"][-1]):
        for field in ("mean_q", "mean_ted", "mean_s"):
            assert field in step

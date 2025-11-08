from __future__ import annotations

from core.forecast_head import ForecastHead
from core.heads import StepFrame
from core.mc_head import MonteCarloHead
from core.regime_head import RegimeChangeHead


def make_frame(t: int, q: float, ted: float, concept: float) -> StepFrame:
    step_features = {
        "concept_fraction": concept,
        "assessment_fraction": 0.1,
        "reading_fraction": 0.2,
    }
    return StepFrame(
        t=t,
        step_id=t,
        obs_edges={(1, 2)},
        cumulative_edges={(1, 2)},
        prev_cumulative={(1, 2)} if t else None,
        node_weights={1: 1.0, 2: 1.0},
        step_features=step_features,
    )


def test_monte_carlo_head_outputs_keys():
    head = MonteCarloHead({"monte_carlo": {"num_samples": 4, "edge_dropout": 0.0}})
    head.init_course("course", {})
    frame = make_frame(0, 0.5, 0.1, 0.6)
    signals = {"q": 0.5, "ted": 0.1}
    result = head.per_step(frame, signals)
    assert "q_mc_mean" in result and "q_mc_std" in result
    summary = head.finalize_course()
    assert "avg_q_mc_std" in summary


def test_forecast_head_predicts_step_types():
    head = ForecastHead({"forecast": {"window_size": 2}})
    head.init_course("course", {})
    frame = make_frame(0, 0.8, 0.1, 0.7)
    res = head.per_step(frame, {"q": 0.8, "ted": 0.1})
    assert "step_type_inferred" in res
    # feed a second step to allow prediction
    head.per_step(make_frame(1, 0.6, 0.2, 0.4), {"q": 0.6, "ted": 0.2})
    summary = head.finalize_course()
    assert "q_trend_slope" in summary


def test_regime_change_head_detects_change():
    head = RegimeChangeHead({"regime_change": {"window": 1, "threshold": 0.05}})
    head.init_course("course", {})
    frames = [
        make_frame(0, 0.3, 0.1, 0.4),
        make_frame(1, 0.35, 0.11, 0.45),
        make_frame(2, 0.9, 0.4, 0.8),
        make_frame(3, 0.92, 0.42, 0.85),
    ]
    res_last = {}
    for idx, fm in enumerate(frames):
        res_last = head.per_step(fm, {"q": fm.step_features["concept_fraction"], "ted": 0.1 * idx})
    assert "change_score" in res_last
    summary = head.finalize_course()
    assert "num_change_points" in summary

from __future__ import annotations

from core.signals import DefaultSignalComputer


def test_ted_uses_jaccard_distance():
    sc = DefaultSignalComputer()

    obs0 = {(1, 2)}
    sig0 = sc.compute(
        step_index=0,
        obs_t=obs0,
        prev_obs=None,
        step_features={},
        core_config={},
    )
    assert sig0.ted == 0.0
    assert sig0.ted_delta is None

    obs1 = {(1, 2), (2, 3)}
    sig1 = sc.compute(
        step_index=1,
        obs_t=obs1,
        prev_obs=obs0,
        step_features={},
        core_config={},
    )
    # intersection=1, union=2 -> TED = 0.5
    assert sig1.ted == 0.5
    assert sig1.ted_delta == 0.5

    obs2 = {(1, 2), (2, 3), (3, 4)}
    sig2 = sc.compute(
        step_index=2,
        obs_t=obs2,
        prev_obs=obs1,
        step_features={},
        core_config={},
    )
    # intersection=2, union=3 -> TED ~= 0.333 -> rounded to 0.333
    assert sig2.ted == 0.333
    assert sig2.ted_delta == round(0.333 - 0.5, 3)


def test_ted_respects_adapter_override():
    sc = DefaultSignalComputer()
    obs = {(1, 2)}
    sig = sc.compute(
        step_index=0,
        obs_t=obs,
        prev_obs=None,
        step_features={"ted": 0.42},
        core_config={},
    )
    assert sig.ted == 0.42

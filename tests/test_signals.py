from __future__ import annotations

from adapters.base import Frame
from core.signals import DefaultSignalComputer, SignalConfig


def make_frame(edges):
    return {tuple(edge) for edge in edges}


def test_spread_single_component_zero():
    config = SignalConfig(compute_spread=True)
    computer = DefaultSignalComputer(config)
    obs = make_frame([(1, 2), (2, 3)])
    signals = computer.compute(
        step_index=0,
        obs_t=obs,
        prev_obs=None,
        step_features={},
        core_config={},
    )
    assert signals.spread == 0.0


def test_spread_multiple_components_positive():
    config = SignalConfig(compute_spread=True)
    computer = DefaultSignalComputer(config)
    obs = make_frame([(1, 2), (3, 4), (5, 6)])
    signals = computer.compute(
        step_index=0,
        obs_t=obs,
        prev_obs=None,
        step_features={},
        core_config={},
    )
    assert signals.spread is not None
    assert signals.spread > 0.0


def test_locality_nodes_detect_degree_change():
    config = SignalConfig(compute_locality=True)
    computer = DefaultSignalComputer(config)

    prev_obs = make_frame([(1, 2), (2, 3)])
    obs = make_frame([(1, 2), (2, 3), (3, 4), (4, 5)])

    computer.compute(
        step_index=0,
        obs_t=prev_obs,
        prev_obs=None,
        step_features={},
        core_config={},
    )
    signals = computer.compute(
        step_index=1,
        obs_t=obs,
        prev_obs=prev_obs,
        step_features={},
        core_config={},
    )

    assert signals.locality_nodes is not None
    assert len(signals.locality_nodes) > 0
    assert signals.locality_nodes[0] in {3, 4, 5}


def test_quality_fallback_uses_weight_mass():
    computer = DefaultSignalComputer()
    obs = make_frame([(1, 2), (2, 3)])
    step_features = {
        "weighted_node_mass": 6.0,
        "unique_node_count": 3,
    }
    signals = computer.compute(
        step_index=0,
        obs_t=obs,
        prev_obs=None,
        step_features=step_features,
        core_config={},
    )
    assert signals.q == 1.0

from __future__ import annotations

from typing import Any, Dict, List, Optional

from adapters.base import Frame
from core.policy import IdentityPolicy, Policy, PolicyConfig, CapacityPolicy
from core.registry import REGISTRY
from core.heads import SignalHead, StepFrame
from core.mc_head import MonteCarloHead
from core.forecast_head import ForecastHead
from core.regime_head import RegimeChangeHead
from core.signals import DefaultSignalComputer, SignalComputer, SignalConfig
from core.state import CoreState

HEAD_REGISTRY = {
    "monte_carlo": MonteCarloHead,
    "forecast": ForecastHead,
    "regime_change": RegimeChangeHead,
}


class Engine:
    """Core runner that replays a dataset through signal computation and policy updates."""

    def __init__(
        self,
        *,
        adapter: str,
        dataset_path: str,
        reporter: str = "insight",
        reporter_kwargs: Optional[Dict[str, Any]] = None,
        adapter_kwargs: Optional[Dict[str, Any]] = None,
        signal_computer: Optional[SignalComputer] = None,
        policy: Optional[Policy] = None,
        core_config: Optional[Dict[str, Any]] = None,
        policy_config: Optional[PolicyConfig] = None,
        signal_config: Optional[SignalConfig] = None,
    ) -> None:
        if adapter not in REGISTRY.adapters:
            raise ValueError(f"Adapter '{adapter}' is not registered")
        if reporter not in REGISTRY.reporters:
            raise ValueError(f"Reporter '{reporter}' is not registered")

        adapter_factory = REGISTRY.adapters[adapter]
        reporter_factory = REGISTRY.reporters[reporter]

        adapter_kwargs = adapter_kwargs or {}
        adapter_kwargs.setdefault("path", dataset_path)

        self.adapter_id = adapter
        self.reporter_name = reporter

        self.stream = adapter_factory(**adapter_kwargs)
        self.reporter = reporter_factory(**(reporter_kwargs or {}))

        self.core_config: Dict[str, Any] = core_config or {}
        self.state = CoreState()
        self.signal_heads: List[SignalHead] = []

        self.signal_computer = signal_computer or DefaultSignalComputer(signal_config)
        self.policy = policy or IdentityPolicy(policy_config)

        head_names = self.core_config.get("heads", [])
        for name in head_names:
            cls = HEAD_REGISTRY.get(name)
            if cls:
                self.signal_heads.append(cls(self.core_config))

    # ------------------------------------------------------------------

    def run(self) -> None:
        meta = getattr(self.stream, "meta", lambda: {})()
        meta = dict(meta)
        meta.setdefault("adapter", self.adapter_id)

        config = {
            "adapter": self.adapter_id,
            "policy": self.policy.__class__.__name__,
            "capacity": self.core_config.get("capacity"),
        }

        self.reporter.start(meta, config)

        prev_pred: Optional[Frame] = None
        prev_cumulative: Optional[Frame] = None
        step_index = 0
        node_weights = getattr(self.stream, "node_weights", {})

        for head in self.signal_heads:
            head.init_course(meta.get("course_id", "course"), meta)

        while self.stream.has_more():
            obs_step = self.stream.next_obs()
            step_id = getattr(self.stream, "current_step", lambda: None)() or step_index
            step_features = getattr(self.stream, "get_step_features", lambda _: {})(
                step_id
            ) or {} 

            cumulative = set(prev_cumulative or set())
            if obs_step:
                cumulative |= obs_step

            signals_obj = self.signal_computer.compute(
                step_index=step_index,
                obs_t=cumulative,
                prev_obs=prev_cumulative,
                step_features=step_features,
                core_config=self.core_config,
            )

            signals: Dict[str, Any] = {
                "q": signals_obj.q,
                "ted": signals_obj.ted,
                "s": signals_obj.stability,
                "ted_delta": signals_obj.ted_delta,
                "spread": signals_obj.spread,
                "locality_nodes": signals_obj.locality_nodes,
                "continuity": step_features.get("continuity"),
            }

            frame_context = StepFrame(
                t=step_index,
                step_id=step_id,
                obs_edges=set(obs_step),
                cumulative_edges=set(cumulative),
                prev_cumulative=set(prev_cumulative) if prev_cumulative else None,
                node_weights=node_weights,
                step_features=step_features,
            )

            for head in self.signal_heads:
                extra = head.per_step(frame_context, signals)
                if extra:
                    signals.update(extra)

            pred = self.policy.step(
                step_index=step_index,
                prev_pred=prev_pred,
                obs_t=obs_step,
                signals=signals,
                core_config=self.core_config,
            )

            step_meta = dict(step_features)
            step_meta["step_id"] = step_id
            step_meta.setdefault("top_nodes", step_features.get("top_nodes", []))
            step_meta.setdefault("commentary", step_features.get("commentary", "Run progressing normally."))
            step_meta.setdefault("counts", step_features.get("counts", {}))

            self.reporter.record(step_index, signals, step_meta, pred=pred, regret=None)

            prev_pred = pred
            prev_cumulative = cumulative
            self.state.record(
                obs_step=obs_step,
                pred=pred,
                cumulative=cumulative,
                history_size=self.core_config.get("history_size", 0),
            )
            step_index += 1

        head_summaries: Dict[str, Dict[str, Any]] = {}
        for head in self.signal_heads:
            summary = head.finalize_course()
            if summary:
                head_summaries[head.name] = summary

        if head_summaries and hasattr(self.reporter, "summary") and isinstance(self.reporter.summary, dict):
            self.reporter.summary["head_summaries"] = head_summaries

        self.reporter.finish()

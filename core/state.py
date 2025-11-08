from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Optional, Set

from adapters.base import Frame
from core.hypotheses import HypothesisManager


@dataclass
class CoreState:
    """
    Minimal core engine state tracking the previous observations/predictions.

    History buffers and hypothesis management are optional and can be expanded later.
    """

    step_index: int = 0
    prev_obs: Optional[Frame] = None
    prev_pred: Optional[Frame] = None
    cumulative_obs: Optional[Frame] = None

    history_obs: Deque[Frame] = field(default_factory=deque)
    history_pred: Deque[Frame] = field(default_factory=deque)

    hypotheses: Optional[HypothesisManager] = None

    def record(
        self,
        *,
        obs_step: Frame,
        pred: Frame,
        cumulative: Frame,
        history_size: int = 0,
    ) -> None:
        self.prev_obs = obs_step
        self.prev_pred = pred
        self.cumulative_obs = cumulative
        if history_size > 0:
            if len(self.history_obs) >= history_size:
                self.history_obs.popleft()
            if len(self.history_pred) >= history_size:
                self.history_pred.popleft()
            self.history_obs.append(obs_step)
            self.history_pred.append(pred)
        self.step_index += 1

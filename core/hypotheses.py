from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from adapters.base import Frame
from core.signals import Signals


@dataclass
class Hypothesis:
    id: str
    members: Set[int] = field(default_factory=set)
    weight: float = 1.0
    status: str = "live"


class HypothesisManager:
    def __init__(self, max_live: int = 3) -> None:
        self.max_live = max_live
        self._hypotheses: Dict[str, Hypothesis] = {}

    def update_from_step(
        self,
        *,
        step_index: int,
        obs_t: Frame,
        pred_t: Frame,
        signals: Signals,
    ) -> None:
        return

    def get_live(self) -> List[Hypothesis]:
        return list(self._hypotheses.values())

    def get_foreground(self) -> Optional[Hypothesis]:
        return None

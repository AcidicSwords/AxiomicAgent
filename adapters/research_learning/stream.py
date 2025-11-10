from __future__ import annotations

from typing import Dict, Optional

from adapters.base import Frame, load_zip_stream
from adapters.research_learning.preprocess import (
    ResearchLearningPreprocessor,
    ResearchLearningPreprocessorConfig,
)
from core.registry import register_adapter


@register_adapter("research_learning")
class ResearchLearningStream:
    def __init__(
        self,
        path: str,
        *,
        preprocessor: Optional[ResearchLearningPreprocessorConfig] = None,
    ):
        raw = load_zip_stream(path)
        processed = ResearchLearningPreprocessor(preprocessor).process(raw)
        self.nodes = processed.nodes
        self.obs_steps = processed.obs_steps
        self.true_steps = processed.true_steps
        self._order = sorted(self.obs_steps)
        self._idx = 0
        self._meta = processed.meta

    def next_obs(self) -> Frame:
        if self._idx >= len(self._order):
            return set()
        step = self._order[self._idx]
        self._idx += 1
        return set(self.obs_steps.get(step, set()))

    def peek_truth(self, horizon: int = 1) -> Optional[Frame]:
        idx = self._idx - 1 + horizon
        if idx < 0 or idx >= len(self._order):
            return None
        step = self._order[idx]
        return set(self.true_steps.get(step, set()))

    def has_more(self) -> bool:
        return self._idx < len(self._order)

    def meta(self) -> Dict[str, object]:
        return dict(self._meta)

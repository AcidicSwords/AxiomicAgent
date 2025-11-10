from __future__ import annotations

from typing import Dict, Optional, Set

from adapters.base import Frame, load_zip_stream
from adapters.conversation_brainstorm.preprocess import (
    ConversationBrainstormPreprocessor,
    ConversationBrainstormPreprocessorConfig,
)
from core.registry import register_adapter


@register_adapter("conversation_brainstorm")
class ConversationBrainstormStream:
    def __init__(
        self,
        path: str,
        *,
        preprocessor: Optional[ConversationBrainstormPreprocessorConfig] = None,
    ):
        raw = load_zip_stream(path)
        processor = ConversationBrainstormPreprocessor(preprocessor)
        processed = processor.process(raw)
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
        step_index = self._idx - 1 + horizon
        if step_index < 0 or step_index >= len(self._order):
            return None
        step = self._order[step_index]
        return set(self.true_steps.get(step, set()))

    def has_more(self) -> bool:
        return self._idx < len(self._order)

    def meta(self) -> Dict[str, object]:
        return dict(self._meta)

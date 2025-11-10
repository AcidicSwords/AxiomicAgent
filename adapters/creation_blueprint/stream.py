from __future__ import annotations

from typing import Dict, Optional

from adapters.base import Frame, load_zip_stream
from adapters.creation_blueprint.preprocess import (
    CreationBlueprintPreprocessor,
    CreationBlueprintPreprocessorConfig,
)
from core.registry import register_adapter


@register_adapter("creation_blueprint")
class CreationBlueprintStream:
    def __init__(
        self,
        path: str,
        *,
        preprocessor: Optional[CreationBlueprintPreprocessorConfig] = None,
    ):
        raw = load_zip_stream(path)
        processed = CreationBlueprintPreprocessor(preprocessor).process(raw)
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

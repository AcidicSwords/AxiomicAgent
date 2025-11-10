from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from adapters.base import ProcessedStream, RawStream


@dataclass
class ConversationBrainstormPreprocessorConfig:
    stop_terms: tuple[str, ...] = ("um", "uh", "like")
    max_degree: int = 80


class ConversationBrainstormPreprocessor:
    """
    Cleans brainstorm graphs before they reach the engine.
    """

    def __init__(self, cfg: ConversationBrainstormPreprocessorConfig | None = None):
        self.cfg = cfg or ConversationBrainstormPreprocessorConfig()

    def process(self, raw: RawStream) -> ProcessedStream:
        # For now, simply mirror raw -> processed. Add filtering logic as needed.
        return ProcessedStream(
            nodes=dict(raw.nodes),
            obs_steps=dict(raw.obs_steps),
            true_steps=dict(raw.true_steps),
            meta=dict(raw.meta),
        )

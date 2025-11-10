from __future__ import annotations

from dataclasses import dataclass

from adapters.base import ProcessedStream, RawStream


@dataclass
class CreationBlueprintPreprocessorConfig:
    max_degree: int = 100


class CreationBlueprintPreprocessor:
    def __init__(self, cfg: CreationBlueprintPreprocessorConfig | None = None):
        self.cfg = cfg or CreationBlueprintPreprocessorConfig()

    def process(self, raw: RawStream) -> ProcessedStream:
        return ProcessedStream(
            nodes=dict(raw.nodes),
            obs_steps=dict(raw.obs_steps),
            true_steps=dict(raw.true_steps),
            meta=dict(raw.meta),
        )

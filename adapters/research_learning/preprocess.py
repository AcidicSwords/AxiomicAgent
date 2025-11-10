from __future__ import annotations

from dataclasses import dataclass

from adapters.base import ProcessedStream, RawStream


@dataclass
class ResearchLearningPreprocessorConfig:
    stop_patterns: tuple[str, ...] = ("^Acknowledgements", "^References")
    topk_per_node: int = 60


class ResearchLearningPreprocessor:
    def __init__(self, cfg: ResearchLearningPreprocessorConfig | None = None):
        self.cfg = cfg or ResearchLearningPreprocessorConfig()

    def process(self, raw: RawStream) -> ProcessedStream:
        return ProcessedStream(
            nodes=dict(raw.nodes),
            obs_steps=dict(raw.obs_steps),
            true_steps=dict(raw.true_steps),
            meta=dict(raw.meta),
        )

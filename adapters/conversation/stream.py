from __future__ import annotations

import os
import os
from pathlib import Path
from typing import Dict, Optional, Union

from core.registry import register_adapter

from adapters.base import Edge, Frame
from adapters.conversation.extractor import extract
from adapters.conversation.preprocess import ConversationPreprocessor
from configs.datasets import ConversationDatasetConfig, load_dataset_config


@register_adapter("conversation_stream")
class ConversationStream:
    def __init__(
        self,
        path: Optional[str] = None,
        *,
        config: Union[str, os.PathLike[str], ConversationDatasetConfig, None] = None,
        scramble: bool = False,
        random_shift: Optional[int] = None,
        stop_terms=None,
    ):
        cfg = self._resolve_config(config)
        if path is None and cfg is not None:
            path = str(cfg.builder.output)

        if path is None:
            raise ValueError("conversation_stream requires path to a conversation zip")
        if not os.path.exists(path):
            raise FileNotFoundError(path)

        raw = extract(path)
        pre = ConversationPreprocessor(config=cfg.preprocessor if cfg else None, stop_terms=stop_terms)
        processed = pre.process(raw)

        self.path = path
        self.scramble = scramble
        self.random_shift = random_shift

        self.nodes: Dict[int, str] = processed.nodes
        self.obs_steps = processed.obs_steps
        self.true_steps = processed.true_steps
        self._steps = sorted(set(self.obs_steps.keys()) | set(self.true_steps.keys()))
        self._idx = 0

        self._meta = dict(processed.meta)
        self._meta.setdefault("steps", len(self._steps))
        self._meta.setdefault("nodes", len(self.nodes))
        self._meta.setdefault("adapter", "conversation_stream")

    def next_obs(self) -> Frame:
        if self._idx >= len(self._steps):
            return set()
        step = self._steps[self._idx]
        obs = set(self.obs_steps.get(step, set()))
        if self.scramble and obs:
            obs = self._scramble(obs)
        self._idx += 1
        return obs

    def peek_truth(self, horizon: int) -> Frame | None:
        if not self.true_steps:
            return None
        idx = self._idx - 1 + horizon
        if idx < 0 or idx >= len(self._steps):
            return None
        step = self._steps[idx]
        if self.random_shift is not None and self._steps:
            step = self._steps[(idx + self.random_shift) % len(self._steps)]
        return set(self.true_steps.get(step, set()))

    def has_more(self) -> bool:
        return self._idx < len(self._steps)

    def meta(self) -> Dict[str, object]:
        return dict(self._meta)

    def node_label(self, node_id: int) -> str:
        return self.nodes.get(node_id, str(node_id))

    def _scramble(self, edges: Frame) -> Frame:
        nodes = {n for e in edges for n in e}
        perm = {n: p for n, p in zip(sorted(nodes), reversed(sorted(nodes)))}
        return {(perm.get(u, u), perm.get(v, v)) for (u, v) in edges}

    @staticmethod
    def _resolve_config(
        config: Union[str, os.PathLike[str], ConversationDatasetConfig, None]
    ) -> Optional[ConversationDatasetConfig]:
        if config is None:
            return None
        if isinstance(config, ConversationDatasetConfig):
            return config
        resolved = load_dataset_config(Path(config))
        if not isinstance(resolved, ConversationDatasetConfig):
            raise ValueError(f"Config {config!r} is not a conversation dataset config")
        return resolved

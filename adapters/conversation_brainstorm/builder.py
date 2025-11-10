from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple

from adapters.base import write_dataset_zip


@dataclass
class ConversationBrainstormBuilderConfig:
    source_glob: str
    output: str
    chunk_minutes: int = 5
    min_turns_per_chunk: int = 6


class ConversationBrainstormBuilder:
    """
    Turns raw brainstorm transcripts into a canonical stream dataset.
    """

    def __init__(self, cfg: ConversationBrainstormBuilderConfig):
        self.cfg = cfg

    def build(self) -> None:
        nodes, edges = self._collect_graph()
        meta = {
            "type": "conversation_brainstorm",
            "chunk_minutes": self.cfg.chunk_minutes,
            "min_turns": self.cfg.min_turns_per_chunk,
        }
        write_dataset_zip(
            Path(self.cfg.output), nodes, edges, meta, node_header="concept"
        )

    def _collect_graph(self) -> Tuple[dict[int, str], List[Tuple[int, int, int]]]:
        """
        Placeholder implementation. In a real builder you would:
        1. Iterate raw transcript files matched by cfg.source_glob
        2. Chunk messages by time window / turn count
        3. Derive nodes (ideas, concerns, decisions) and edges (co-occurrence)
        """
        nodes: dict[int, str] = {}
        edges: List[Tuple[int, int, int]] = []
        for idx, path in enumerate(self._iter_sources()):
            nodes[idx] = path.stem
            edges.append((idx, idx, idx))
        return nodes, edges

    def _iter_sources(self) -> Iterable[Path]:
        return Path(".").glob(self.cfg.source_glob)

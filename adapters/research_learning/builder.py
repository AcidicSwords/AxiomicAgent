from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from adapters.base import write_dataset_zip


@dataclass
class ResearchLearningBuilderConfig:
    source_root: str
    output: str
    section_glob: str = "**/*.md"
    max_steps: int = 300


class ResearchLearningBuilder:
    """
    Converts structured learning materials (notes, outlines) into stepwise graphs.
    """

    def __init__(self, cfg: ResearchLearningBuilderConfig):
        self.cfg = cfg

    def build(self) -> None:
        nodes, edges = self._parse_sections()
        meta = {"type": "research_learning", "source": self.cfg.source_root}
        write_dataset_zip(Path(self.cfg.output), nodes, edges, meta, node_header="topic")

    def _parse_sections(self) -> Tuple[Dict[int, str], List[Tuple[int, int, int]]]:
        nodes: Dict[int, str] = {}
        edges: List[Tuple[int, int, int]] = []
        for idx, section in enumerate(self._iter_sections()):
            nodes[idx] = section
            edges.append((idx, idx, idx))
        return nodes, edges

    def _iter_sections(self) -> Iterable[str]:
        for path in Path(self.cfg.source_root).glob(self.cfg.section_glob):
            yield path.stem

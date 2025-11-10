from __future__ import annotations

import yaml
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from adapters.base import write_dataset_zip


@dataclass
class CreationBlueprintBuilderConfig:
    source_root: str
    output: str
    version_glob: str = "v*/design.yaml"


class CreationBlueprintBuilder:
    """
    Converts versioned blueprint documents into stream steps.
    """

    def __init__(self, cfg: CreationBlueprintBuilderConfig):
        self.cfg = cfg

    def build(self) -> None:
        nodes, edges = self._collect_versions()
        meta = {"type": "creation_blueprint"}
        write_dataset_zip(Path(self.cfg.output), nodes, edges, meta, node_header="entity")

    def _collect_versions(self) -> Tuple[Dict[int, str], List[Tuple[int, int, int]]]:
        nodes: Dict[int, str] = {}
        edges: List[Tuple[int, int, int]] = []
        versions = sorted(Path(self.cfg.source_root).glob(self.cfg.version_glob))
        for step_idx, version_path in enumerate(versions):
            try:
                data = yaml.safe_load(version_path.read_text(encoding="utf-8"))
            except FileNotFoundError:
                continue
            nodes[step_idx] = version_path.stem
            edges.append((step_idx, step_idx, step_idx))
        return nodes, edges

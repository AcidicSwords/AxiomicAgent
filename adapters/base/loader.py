from __future__ import annotations

import csv
import io
import json
import zipfile
from pathlib import Path
from typing import Dict

from .types import Edge, Frame, RawStream


def load_zip_stream(path: str | Path) -> RawStream:
    """
    Minimal zip loader. Expects nodes.csv, edges_obs.csv, optional edges_true.csv, meta.json.
    """
    path = Path(path)
    nodes: Dict[int, str] = {}
    obs_steps: Dict[int, Frame] = {}
    true_steps: Dict[int, Frame] = {}
    meta: Dict[str, object] = {}

    def _read_nodes(reader):
        for row in reader:
            nodes[int(row["id"])] = row[next(col for col in row if col != "id")]

    def _read_edges(reader, target):
        for row in reader:
            step = int(row["step"])
            edge: Edge = (int(row["src"]), int(row["dst"]))
            target.setdefault(step, set()).add(edge)

    if path.is_dir():
        with (path / "nodes.csv").open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            _read_nodes(reader)
        with (path / "edges_obs.csv").open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            _read_edges(reader, obs_steps)
        true_file = path / "edges_true.csv"
        if true_file.exists():
            with true_file.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                _read_edges(reader, true_steps)
        meta_file = path / "meta.json"
        if meta_file.exists():
            with meta_file.open("r", encoding="utf-8") as f:
                meta = json.loads(f.read())
    else:
        with zipfile.ZipFile(path, "r") as zf:
            with zf.open("nodes.csv") as f:
                reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8"))
                _read_nodes(reader)

            with zf.open("edges_obs.csv") as f:
                reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8"))
                _read_edges(reader, obs_steps)

            if "edges_true.csv" in zf.namelist():
                with zf.open("edges_true.csv") as f:
                    reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8"))
                    _read_edges(reader, true_steps)

            if "meta.json" in zf.namelist():
                with zf.open("meta.json") as f:
                    meta = json.loads(io.TextIOWrapper(f, encoding="utf-8").read())

    meta.setdefault("dataset_path", str(path))
    return RawStream(nodes=nodes, obs_steps=obs_steps, true_steps=true_steps, meta=meta)

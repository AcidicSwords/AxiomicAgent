from __future__ import annotations

import csv
import json
import zipfile
from pathlib import Path
from typing import Any, Dict, List

from .types import Edge, Frame, RawStream


def load_zip_stream(path: str | Path) -> RawStream:
    path = Path(path)
    nodes: Dict[int, Dict[str, Any]] = {}
    obs_steps: Dict[int, Frame] = {}
    true_steps: Dict[int, Frame] = {}
    meta: Dict[str, object] = {}

    with zipfile.ZipFile(path, "r") as zf:
        with zf.open("nodes.csv") as f:
            reader = csv.DictReader((line.decode("utf-8") for line in f))
            for row in reader:
                node_id = int(row["id"])
                nodes[node_id] = {key: value for key, value in row.items()}

        with zf.open("edges_obs.csv") as f:
            reader = csv.DictReader((line.decode("utf-8") for line in f))
            for row in reader:
                step = int(row["step"])
                edge: Edge = (int(row["src"]), int(row["dst"]))
                obs_steps.setdefault(step, set()).add(edge)

        if "edges_true.csv" in zf.namelist():
            with zf.open("edges_true.csv") as f:
                reader = csv.DictReader((line.decode("utf-8") for line in f))
                for row in reader:
                    step = int(row["step"])
                    edge = (int(row["src"]), int(row["dst"]))
                    true_steps.setdefault(step, set()).add(edge)

        if "meta.json" in zf.namelist():
            with zf.open("meta.json") as f:
                meta = json.loads(f.read().decode("utf-8"))

    meta.setdefault("dataset_path", str(path))
    return RawStream(nodes=nodes, obs_steps=obs_steps, true_steps=true_steps, meta=meta)

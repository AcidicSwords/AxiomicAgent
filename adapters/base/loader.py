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


def load_fs_stream(dir_path: str | Path) -> RawStream:
    """Load a RawStream from an unpacked dataset directory.

    Expects files: nodes.csv, edges_obs.csv, optional edges_true.csv, optional meta.json
    """
    dir_path = Path(dir_path)
    if not dir_path.exists() or not dir_path.is_dir():
        raise FileNotFoundError(dir_path)

    nodes: Dict[int, Dict[str, Any]] = {}
    obs_steps: Dict[int, Frame] = {}
    true_steps: Dict[int, Frame] = {}
    meta: Dict[str, Any] = {}

    nodes_csv = dir_path / "nodes.csv"
    edges_obs_csv = dir_path / "edges_obs.csv"
    edges_true_csv = dir_path / "edges_true.csv"
    meta_json = dir_path / "meta.json"

    if not nodes_csv.exists() or not edges_obs_csv.exists():
        raise FileNotFoundError(f"Missing required dataset files in {dir_path}")

    with nodes_csv.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            node_id = int(row["id"])
            nodes[node_id] = {key: value for key, value in row.items()}

    with edges_obs_csv.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            step = int(row["step"])
            edge: Edge = (int(row["src"]), int(row["dst"]))
            obs_steps.setdefault(step, set()).add(edge)

    if edges_true_csv.exists():
        with edges_true_csv.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                step = int(row["step"])
                edge = (int(row["src"]), int(row["dst"]))
                true_steps.setdefault(step, set()).add(edge)

    if meta_json.exists():
        with meta_json.open("r", encoding="utf-8") as f:
            meta = json.load(f)

    meta.setdefault("dataset_path", str(dir_path))
    return RawStream(nodes=nodes, obs_steps=obs_steps, true_steps=true_steps, meta=meta)

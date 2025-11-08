#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List, Tuple


def read_edges_by_step(ds_dir: Path) -> Dict[int, List[Tuple[int, int]]]:
    edges_file = ds_dir / "edges_obs.csv"
    if not edges_file.exists():
        return {}
    by_step: Dict[int, List[Tuple[int, int]]] = {}
    with edges_file.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # accept either step or step_id or step_id column variants
        step_key = "step" if "step" in reader.fieldnames else ("step_id" if "step_id" in reader.fieldnames else None)
        if step_key is None:
            return {}
        for row in reader:
            try:
                s = int(row.get(step_key) or 0)
                src = int(row.get("from_node_id") or row.get("src") or 0)
                dst = int(row.get("to_node_id") or row.get("dst") or 0)
                by_step.setdefault(s, []).append((src, dst))
            except Exception:
                continue
    return by_step


def unit_count(edges: List[Tuple[int, int]]) -> int:
    try:
        import networkx as nx  # type: ignore
    except Exception:
        # fallback: unique component count via union find-ish
        nodes = set()
        for a, b in edges:
            nodes.add(a); nodes.add(b)
        return max(1, len(nodes) // 5)
    G = nx.Graph()
    G.add_edges_from(edges)
    if G.number_of_nodes() == 0:
        return 0
    # Try communities; fallback to connected components
    try:
        from networkx.algorithms.community import greedy_modularity_communities
        comms = list(greedy_modularity_communities(G))
        return max(1, len(comms))
    except Exception:
        return max(1, nx.number_connected_components(G))


def main() -> None:
    ap = argparse.ArgumentParser(description="Compute simple unit counts per course from FS datasets")
    ap.add_argument("--fs-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    fs_root = Path(args.fs_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for ds in fs_root.iterdir():
        if not ds.is_dir():
            continue
        edges_by_step = read_edges_by_step(ds)
        if not edges_by_step:
            continue
        per_step = {int(s): unit_count(e) for s, e in edges_by_step.items()}
        summary = {
            "dataset": ds.name,
            "avg_unit_count": sum(per_step.values()) / max(1, len(per_step)),
            "per_step": per_step,
        }
        (out_dir / f"{ds.name}.units.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()


from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Dict, Iterable, Tuple


def write_dataset_zip(
    out_path: Path,
    nodes: Dict[int, str],
    edges: Iterable[Tuple[int, int, int]],
    meta: Dict[str, object],
    *,
    node_header: str,
) -> None:
    """
    Write nodes/edges/meta in the canonical Axiom stream format.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        node_lines = [f"id,{node_header}"] + [
            f"{nid},{nodes[nid]}" for nid in sorted(nodes)
        ]
        zf.writestr("nodes.csv", "\n".join(node_lines))

        edge_lines = ["step,src,dst,val"] + [
            f"{step},{src},{dst},1" for step, src, dst in edges
        ]
        zf.writestr("edges_obs.csv", "\n".join(edge_lines))
        zf.writestr("meta.json", json.dumps(meta, indent=2))

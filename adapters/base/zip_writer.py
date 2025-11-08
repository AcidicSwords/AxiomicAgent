from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Sequence, Tuple


def write_dataset_zip(
    out_path: Path,
    nodes: Any,
    edges: Iterable[Any],
    meta: Dict[str, object],
    *,  # keyword-only
    node_fields: Sequence[str] | None = None,
    edge_fields: Sequence[str] | None = None,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        node_csv = _serialize_nodes(nodes, node_fields=node_fields)
        edge_csv = _serialize_edges(edges, edge_fields=edge_fields)
        zf.writestr("nodes.csv", node_csv)
        zf.writestr("edges_obs.csv", edge_csv)
        zf.writestr("meta.json", json.dumps(meta, indent=2))


def _serialize_nodes(nodes: Any, *, node_fields: Sequence[str] | None) -> str:
    if node_fields is None:
        if not isinstance(nodes, Mapping):
            raise TypeError("nodes must be a mapping when node_fields is None")
        header = "id,label"
        rows = [f"{nid},{nodes[nid]}" for nid in sorted(nodes)]
        return "\n".join([header] + rows)

    node_rows: list[str] = []
    header = ",".join(node_fields)
    for entry in nodes:
        row = []
        for field in node_fields:
            value = entry.get(field, "")
            if value is None:
                value = ""
            row.append(str(value).replace("\n", " ").replace("\r", " "))
        node_rows.append(",".join(row))
    return "\n".join([header] + node_rows)


def _serialize_edges(edges: Iterable[Any], *, edge_fields: Sequence[str] | None) -> str:
    default_fields = ("step", "src", "dst", "val")
    fields = edge_fields or default_fields

    rows: list[str] = []
    for entry in edges:
        if isinstance(entry, Mapping):
            row = []
            for field in fields:
                value = entry.get(field, 1 if field == "val" else "")
                if field == "val" and value == "":
                    value = 1
                row.append(str(value))
        else:
            # treat as tuple (step, src, dst)
            step, src, dst = entry
            row = [str(step), str(src), str(dst), "1"]
        rows.append(",".join(row))

    header = ",".join(fields if edge_fields else default_fields)
    return "\n".join([header] + rows)

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

from adapters.base import write_dataset_zip


@dataclass
class CreationBlueprintBuilderConfig:
    treat_process_steps_as_nodes: bool = True
    include_requirement_to_component_edges: bool = True


def build_dataset_from_json(
    input_paths: Sequence[Path],
    output_zip: Path,
    config: Optional[CreationBlueprintBuilderConfig] = None,
) -> None:
    cfg = config or CreationBlueprintBuilderConfig()
    specs = [_load_spec(path) for path in input_paths]
    if not specs:
        raise ValueError("No blueprint specs provided.")

    nodes, edges = _build_nodes_edges(specs, cfg)
    meta = {
        "adapter": "creation_blueprint",
        "num_specs": len(specs),
        "num_nodes": len(nodes),
        "step_semantics": "static_spec",
        "source_files": [str(path) for path in input_paths],
        "config": {
            "treat_process_steps_as_nodes": cfg.treat_process_steps_as_nodes,
            "include_requirement_to_component_edges": cfg.include_requirement_to_component_edges,
        },
    }

    write_dataset_zip(
        output_zip,
        nodes,
        edges,
        meta,
        node_fields=("id", "label", "raw_type", "spec_id", "origin"),
        edge_fields=("step", "src", "dst", "val", "relation"),
    )


def _load_spec(path: Path) -> Dict[str, object]:
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    data.setdefault("requirements", [])
    data.setdefault("components", [])
    data.setdefault("processes", [])
    data.setdefault("links", [])
    data["spec_id"] = data.get("spec_id") or path.stem
    return data


def _build_nodes_edges(
    specs: Sequence[Dict[str, object]],
    cfg: CreationBlueprintBuilderConfig,
):
    nodes: List[Dict[str, object]] = []
    edges: List[Dict[str, object]] = []
    node_index: Dict[str, int] = {}

    def register_node(key: str, data: Dict[str, object]) -> int:
        if key not in node_index:
            node_index[key] = len(node_index)
            nodes.append({"id": node_index[key], **data})
        return node_index[key]

    # ------------------------------------------------------------------ nodes
    for spec in specs:
        spec_id = str(spec.get("spec_id"))

        for idx, req in enumerate(spec.get("requirements", [])):
            key = f"{spec_id}::requirement::{idx}"
            register_node(
                key,
                {
                    "label": str(req),
                    "raw_type": "requirement",
                    "spec_id": spec_id,
                    "origin": "requirements",
                },
            )

        for component in spec.get("components", []):
            key = f"{spec_id}::component::{component}"
            register_node(
                key,
                {
                    "label": str(component),
                    "raw_type": "component",
                    "spec_id": spec_id,
                    "origin": "components",
                },
            )

        if cfg.treat_process_steps_as_nodes:
            for process in spec.get("processes", []):
                process_name = process.get("name", "")
                for step_name in process.get("steps", []):
                    key = f"{spec_id}::process_step::{process_name}::{step_name}"
                    register_node(
                        key,
                        {
                            "label": str(step_name),
                            "raw_type": "process_step",
                            "spec_id": spec_id,
                            "origin": process_name or "process",
                        },
                    )

    # ------------------------------------------------------------------ edges
    step_counter = 0

    for spec in specs:
        spec_id = str(spec.get("spec_id"))

        component_keys = {
            component: node_index[f"{spec_id}::component::{component}"]
            for component in spec.get("components", [])
            if f"{spec_id}::component::{component}" in node_index
        }

        if cfg.include_requirement_to_component_edges:
            requirements = list(enumerate(spec.get("requirements", [])))
            for req_idx, req_text in requirements:
                req_key = f"{spec_id}::requirement::{req_idx}"
                if req_key not in node_index:
                    continue
                targets = _match_requirement_to_components(req_text, component_keys)
                for component_name in targets:
                    edges.append(
                        {
                            "step": step_counter,
                            "src": node_index[req_key],
                            "dst": component_keys[component_name],
                            "val": 1,
                            "relation": "satisfied_by",
                        }
                    )
                    step_counter += 1

        for link in spec.get("links", []):
            src = link.get("from")
            dst = link.get("to")
            relation = link.get("relation", "links_to")
            src_key = f"{spec_id}::component::{src}"
            dst_key = f"{spec_id}::component::{dst}"
            if src_key in node_index and dst_key in node_index:
                edges.append(
                    {
                        "step": step_counter,
                        "src": node_index[src_key],
                        "dst": node_index[dst_key],
                        "val": 1,
                        "relation": relation,
                    }
                )
                step_counter += 1

        if cfg.treat_process_steps_as_nodes:
            for process in spec.get("processes", []):
                process_name = process.get("name", "")
                steps = [str(step) for step in process.get("steps", [])]
                for prev, curr in zip(steps, steps[1:]):
                    prev_key = f"{spec_id}::process_step::{process_name}::{prev}"
                    curr_key = f"{spec_id}::process_step::{process_name}::{curr}"
                    if prev_key in node_index and curr_key in node_index:
                        edges.append(
                            {
                                "step": step_counter,
                                "src": node_index[prev_key],
                                "dst": node_index[curr_key],
                                "val": 1,
                                "relation": f"{process_name or 'process'}",
                            }
                        )
                        step_counter += 1

    return nodes, edges


def _match_requirement_to_components(
    requirement_text: str,
    components: Dict[str, int],
) -> Iterable[str]:
    """Return component names linked to a requirement via simple keyword matching."""
    text = requirement_text.lower()
    matched: List[str] = []
    for component_name in components:
        name_lower = component_name.lower()
        if name_lower in text:
            matched.append(component_name)
            continue

        if "password" in text and "auth" in name_lower:
            matched.append(component_name)
        elif ("2fa" in text or "two-factor" in text) and ("auth" in name_lower or "notification" in name_lower):
            matched.append(component_name)

    if not matched and components:
        # Fall back to linking the first component to ensure coverage
        matched.append(next(iter(components)))
    return matched

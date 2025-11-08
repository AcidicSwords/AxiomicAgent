from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

from adapters.base import write_dataset_zip


# ---------------------------------------------------------------------------
# Activity mode


@dataclass
class ResearchActivityBuilderConfig:
    min_events_per_user: int = 3
    max_users: Optional[int] = None
    max_events_per_user: Optional[int] = None
    event_types_of_interest: Optional[Sequence[str]] = None


def build_dataset_from_activity_logs(
    input_paths: Sequence[Path],
    output_zip: Path,
    config: Optional[ResearchActivityBuilderConfig] = None,
) -> None:
    cfg = config or ResearchActivityBuilderConfig()
    events = _load_activity_events(input_paths, cfg)
    if not events:
        raise ValueError("No activity events found in the provided input.")

    nodes, edges = _activity_nodes_edges(events)
    meta = {
        "adapter": "research_learning",
        "mode": "activity",
        "num_users": len({event["user_id"] for event in events}),
        "num_events": len(events),
        "num_resources": len(nodes),
        "step_semantics": "chronological_event_transition",
        "source_files": [str(path) for path in input_paths],
        "config": {
            "min_events_per_user": cfg.min_events_per_user,
            "max_users": cfg.max_users,
            "max_events_per_user": cfg.max_events_per_user,
            "event_types_of_interest": list(cfg.event_types_of_interest or []),
        },
    }

    write_dataset_zip(
        output_zip,
        nodes,
        edges,
        meta,
        node_fields=("id", "resource_id", "resource_label", "course_id"),
        edge_fields=("step", "src", "dst", "val", "user_id", "event_type"),
    )


def _load_activity_events(
    input_paths: Sequence[Path],
    cfg: ResearchActivityBuilderConfig,
) -> List[Dict[str, object]]:
    events: List[Dict[str, object]] = []

    for path in input_paths:
        with Path(path).open("r", encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                payload = json.loads(line)
                event_type = str(payload.get("event_type", ""))

                if cfg.event_types_of_interest and event_type not in cfg.event_types_of_interest:
                    continue

                events.append(
                    {
                        "user_id": str(payload["user_id"]),
                        "timestamp": str(payload["timestamp"]),
                        "resource_id": str(payload["resource_id"]),
                        "resource_label": str(payload.get("resource_label", payload.get("resource_id"))),
                        "event_type": event_type,
                        "score": payload.get("score"),
                        "course_id": str(payload.get("course_id", "")),
                    }
                )

    events.sort(key=lambda e: (e["user_id"], e["timestamp"]))

    filtered_events: List[Dict[str, object]] = []
    grouped: Dict[str, List[Dict[str, object]]] = {}
    for event in events:
        grouped.setdefault(event["user_id"], []).append(event)

    if cfg.max_users is not None:
        allowed_users = sorted(grouped)[: cfg.max_users]
        grouped = {uid: grouped[uid] for uid in allowed_users}

    for user_id, user_events in grouped.items():
        if len(user_events) < cfg.min_events_per_user:
            continue
        if cfg.max_events_per_user is not None:
            user_events = user_events[: cfg.max_events_per_user]
        filtered_events.extend(user_events)

    filtered_events.sort(key=lambda e: (e["timestamp"], e["user_id"]))
    return filtered_events


def _activity_nodes_edges(events: List[Dict[str, object]]):
    resource_index: Dict[str, int] = {}
    nodes: List[Dict[str, object]] = []

    for resource_id in {event["resource_id"] for event in events}:
        resource_index[resource_id] = len(resource_index)

    for resource_id, node_id in resource_index.items():
        example_event = next(ev for ev in events if ev["resource_id"] == resource_id)
        nodes.append(
            {
                "id": node_id,
                "resource_id": resource_id,
                "resource_label": example_event["resource_label"],
                "course_id": example_event.get("course_id", ""),
            }
        )

    edges: List[Dict[str, object]] = []
    step = 0
    events_by_user: Dict[str, List[Dict[str, object]]] = {}
    for event in events:
        events_by_user.setdefault(event["user_id"], []).append(event)

    for user_id, user_events in events_by_user.items():
        user_events.sort(key=lambda e: e["timestamp"])
        for prev, curr in zip(user_events, user_events[1:]):
            edges.append(
                {
                    "step": step,
                    "src": resource_index[prev["resource_id"]],
                    "dst": resource_index[curr["resource_id"]],
                    "val": 1,
                    "user_id": user_id,
                    "event_type": curr["event_type"],
                }
            )
            step += 1

    return nodes, edges


# ---------------------------------------------------------------------------
# Corpus mode


@dataclass
class ResearchCorpusBuilderConfig:
    include_section_nodes: bool = True
    include_doc_edges: bool = True
    include_within_doc_order: bool = True
    max_docs: Optional[int] = None


def build_dataset_from_corpus_json(
    input_paths: Sequence[Path],
    output_zip: Path,
    config: Optional[ResearchCorpusBuilderConfig] = None,
) -> None:
    cfg = config or ResearchCorpusBuilderConfig()
    documents = _load_corpus(input_paths, cfg)
    if not documents:
        raise ValueError("No documents found in corpus input.")

    nodes, edges = _corpus_nodes_edges(documents, cfg)
    meta = {
        "adapter": "research_learning",
        "mode": "corpus",
        "num_docs": len({node["doc_id"] for node in nodes if node["raw_type"].startswith("doc")}),
        "num_sections": len([n for n in nodes if n["raw_type"] == "section"]),
        "step_semantics": "static_corpus",
        "source_files": [str(p) for p in input_paths],
        "config": {
            "include_section_nodes": cfg.include_section_nodes,
            "include_doc_edges": cfg.include_doc_edges,
            "include_within_doc_order": cfg.include_within_doc_order,
            "max_docs": cfg.max_docs,
        },
    }

    write_dataset_zip(
        output_zip,
        nodes,
        edges,
        meta,
        node_fields=("id", "label", "raw_type", "doc_id", "section_id"),
        edge_fields=("step", "src", "dst", "val", "relation"),
    )


def _load_corpus(
    input_paths: Sequence[Path],
    cfg: ResearchCorpusBuilderConfig,
) -> List[Dict[str, object]]:
    documents: List[Dict[str, object]] = []
    for path in input_paths:
        data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
        if isinstance(data, dict):
            documents.append(data)
        else:
            documents.extend(data)

    if cfg.max_docs is not None:
        documents = documents[: cfg.max_docs]
    return documents


def _corpus_nodes_edges(
    documents: List[Dict[str, object]],
    cfg: ResearchCorpusBuilderConfig,
):
    nodes: List[Dict[str, object]] = []
    edges: List[Dict[str, object]] = []
    node_index: Dict[str, int] = {}

    def register_node(key: str, data: Dict[str, object]) -> int:
        if key not in node_index:
            node_index[key] = len(node_index)
            nodes.append({"id": node_index[key], **data})
        return node_index[key]

    for doc in documents:
        doc_key = f"doc::{doc['doc_id']}"
        register_node(
            doc_key,
            {
                "label": doc.get("title", doc["doc_id"]),
                "raw_type": f"doc:{doc.get('kind', 'unknown')}",
                "doc_id": doc["doc_id"],
                "section_id": "",
            },
        )

        sections = doc.get("sections", []) or []
        if cfg.include_section_nodes:
            for section in sections:
                section_key = f"section::{doc['doc_id']}::{section.get('section_id', '')}"
                register_node(
                    section_key,
                    {
                        "label": section.get("title", ""),
                        "raw_type": "section",
                        "doc_id": doc["doc_id"],
                        "section_id": section.get("section_id", ""),
                    },
                )

    # edges
    step = 0
    for doc in documents:
        doc_key = f"doc::{doc['doc_id']}"
        doc_id = node_index[doc_key]

        sections = doc.get("sections", []) or []
        if cfg.include_doc_edges:
            for section in sections:
                for target in section.get("outlinks", []) or []:
                    if f"doc::{target}" in node_index:
                        edges.append(
                            {
                                "step": step,
                                "src": doc_id,
                                "dst": node_index[f"doc::{target}"],
                                "val": 1,
                                "relation": "outlink",
                            }
                        )
                        step += 1

        if cfg.include_section_nodes:
            ordered_sections = [
                node_index[f"section::{doc['doc_id']}::{section.get('section_id', '')}"]
                for section in sections
                if f"section::{doc['doc_id']}::{section.get('section_id', '')}" in node_index
            ]
            if cfg.include_within_doc_order:
                for prev, curr in zip(ordered_sections, ordered_sections[1:]):
                    edges.append(
                        {
                            "step": step,
                            "src": prev,
                            "dst": curr,
                            "val": 1,
                            "relation": "section_order",
                        }
                    )
                    step += 1

    return nodes, edges

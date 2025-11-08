#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set

from adapters.base.zip_writer import write_dataset_zip
from adapters.conversation.extractors import AdvancedNodeExtractor, SimpleEdgeBuilder, SimpleNodeExtractor
from adapters.conversation.types import ConversationNode


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower())
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug or "conversation"


class ConversationDatasetBuilder:
    def __init__(self, window_size: int = 6):
        self.window_size = max(1, window_size)
        try:
            self.extractor = AdvancedNodeExtractor()
        except Exception:
            self.extractor = SimpleNodeExtractor()
        self.edge_builder = SimpleEdgeBuilder()

    def build(self, transcript_path: Path, output_zip: Path, course_id: str) -> None:
        data = json.loads(transcript_path.read_text(encoding="utf-8"))
        transcript = data.get("transcript") or data.get("turns") or []
        clean_title = str(data.get("title") or transcript_path.stem)
        nodes: List[Dict[str, object]] = []
        edges: List[Dict[str, object]] = []
        node_map: Dict[str, int] = {}
        node_counter = 0
        prev_nodes: List[ConversationNode] = []
        prev_text = ""
        speakers_overall: Set[str] = set()

        step_meta: Dict[int, Dict[str, object]] = defaultdict(
            lambda: {
                "reply_edges": 0,
                "adjacency_edges": 0,
                "question_count": 0,
                "turn_count": 0,
                "speakers": set(),
            }
        )

        for turn_index, entry in enumerate(transcript):
            text = str(entry.get("text") or entry.get("content") or "").strip()
            if not text:
                continue
            speaker = str(entry.get("speaker") or entry.get("actor") or f"speaker_{turn_index}")
            role = "assistant" if turn_index % 2 else "user"
            step_id = turn_index // self.window_size
            step_meta[step_id]["turn_count"] += 1
            step_meta[step_id]["speakers"].add(speaker)
            speakers_overall.add(speaker)

            current_nodes = self.extractor.extract_nodes(text, role=role, turn_index=turn_index)
            if not current_nodes:
                fallback = self.extractor._create_node(text, "concept", role, turn_index, metadata={"speaker": speaker})
                current_nodes = [fallback]

            for node in current_nodes:
                if node.id not in node_map:
                    node_map[node.id] = node_counter
                    node_entry = {
                        "id": node_counter,
                        "label": node.text,
                        "kind": node.type,
                        "role": node.role,
                        "speaker": speaker,
                        "turn_index": turn_index,
                        "course_id": course_id,
                        "source_file": str(transcript_path.name),
                    }
                    nodes.append(node_entry)
                    node_counter += 1
                    if node.type == "question":
                        step_meta[step_id]["question_count"] += 1

            edges_raw = self.edge_builder.build_edges(
                current_nodes=current_nodes,
                previous_nodes=prev_nodes,
                current_text=text,
                previous_text=prev_text,
                turn_index=turn_index,
            )
            step_meta[step_id]["adjacency_edges"] += len(edges_raw)

            for edge in edges_raw:
                src = node_map.get(edge.source)
                dst = node_map.get(edge.target)
                if src is None or dst is None:
                    continue
                if edge.type == "reply":
                    step_meta[step_id]["reply_edges"] += 1
                edges.append({"step": step_id, "src": src, "dst": dst, "type": edge.type, "weight": round(edge.weight or edge.quality or 1.0, 3)})

            prev_nodes = current_nodes
            prev_text = text

        if not nodes:
            raise SystemExit(f"No nodes extracted from {transcript_path}")

        step_features: Dict[int, Dict[str, object]] = {}
        for step_id, meta_dict in step_meta.items():
            adjacency_edges = int(meta_dict["adjacency_edges"])
            reply_edges = int(meta_dict["reply_edges"])
            turn_count = int(meta_dict["turn_count"])
            question_count = int(meta_dict["question_count"])
            speakers = sorted(meta_dict["speakers"])
            ratio = round(reply_edges / max(adjacency_edges, 1), 3) if adjacency_edges else 0.0
            density = round(question_count / max(turn_count, 1), 3)
            step_features[step_id] = {
                "reply_edges": reply_edges,
                "adjacency_edges": adjacency_edges,
                "turn_count": turn_count,
                "question_count": question_count,
                "speakers": speakers,
                "adjacency_ratio": ratio,
                "speaker_count": len(speakers),
                "question_density": density,
            }

        meta = {
            "course_id": course_id,
            "domain": "conversation",
            "window_size": self.window_size,
            "source_file": str(transcript_path.name),
            "title": clean_title,
            "step_features": {str(step): feats for step, feats in step_features.items()},
            "speakers": sorted(speakers_overall),
            "turns": len(transcript),
        }
        write_dataset_zip(
            output_zip,
            nodes=nodes,
            edges=edges,
            meta=meta,
            node_fields=["id", "label", "kind", "role", "speaker", "turn_index", "course_id", "source_file"],
            edge_fields=["step", "src", "dst", "type", "weight"],
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build curriculum-like datasets from cleaned conversation transcripts")
    parser.add_argument("--input-dir", default="reports/conversation_clean", help="Directory with cleaned JSON transcripts")
    parser.add_argument("--output-dir", default="datasets/mit_curriculum_datasets", help="Where to write ZIP datasets")
    parser.add_argument("--window-size", type=int, default=6, help="Number of turns per step")
    parser.add_argument("--prefix", default="conversation", help="Prefix for generated dataset IDs")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    if not input_dir.exists():
        raise SystemExit(f"Conversation input path does not exist: {input_dir}")

    builder = ConversationDatasetBuilder(window_size=args.window_size)
    output_dir.mkdir(parents=True, exist_ok=True)
    for transcript_path in sorted(input_dir.glob("*.json")):
        stem = transcript_path.stem
        course_id = f"{args.prefix}_{_slugify(stem)}"
        out_zip = output_dir / f"{course_id}.zip"
        builder.build(transcript_path, out_zip, course_id)
        print(f"Wrote conversation dataset {out_zip}")


if __name__ == "__main__":
    main()

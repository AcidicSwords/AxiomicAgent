from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from adapters.base import write_dataset_zip


@dataclass
class ConversationBuilderConfig:
    min_turn_tokens: int = 1
    max_sessions: Optional[int] = None
    max_turns_per_session: Optional[int] = None


@dataclass
class TurnRecord:
    session_id: str
    turn_index: int
    speaker: str
    text: str


def build_dataset_from_jsonl(
    input_paths: Sequence[Path],
    output_zip: Path,
    config: Optional[ConversationBuilderConfig] = None,
) -> None:
    """
    Build a conversation_brainstorm dataset from one or more JSONL files.

    Each line in the input is expected to be a JSON object with fields:
        session_id, turn_index, speaker, text
    """

    cfg = config or ConversationBuilderConfig()
    turns = _load_turns(input_paths, cfg)
    if not turns:
        raise ValueError("No conversation turns found in the provided input.")

    nodes, edges = _build_nodes_edges(turns)
    meta = {
        "adapter": "conversation_brainstorm",
        "num_sessions": len({t.session_id for t in turns}),
        "num_turns": len(turns),
        "step_semantics": "turn",
        "source_files": [str(path) for path in input_paths],
        "config": {
            "min_turn_tokens": cfg.min_turn_tokens,
            "max_sessions": cfg.max_sessions,
            "max_turns_per_session": cfg.max_turns_per_session,
        },
    }

    write_dataset_zip(
        output_zip,
        nodes,
        edges,
        meta,
        node_fields=("id", "session_id", "turn_index", "speaker", "text"),
        edge_fields=("step", "src", "dst", "val"),
    )


def _load_turns(
    input_paths: Sequence[Path],
    cfg: ConversationBuilderConfig,
) -> List[TurnRecord]:
    by_session: Dict[str, List[TurnRecord]] = {}

    for path in input_paths:
        with Path(path).open("r", encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                payload = json.loads(line)
                record = TurnRecord(
                    session_id=str(payload["session_id"]),
                    turn_index=int(payload["turn_index"]),
                    speaker=str(payload.get("speaker", "")),
                    text=str(payload.get("text", "")).strip(),
                )

                if cfg.min_turn_tokens and _token_count(record.text) < cfg.min_turn_tokens:
                    continue

                by_session.setdefault(record.session_id, []).append(record)

    if cfg.max_sessions is not None:
        allowed_sessions = sorted(by_session)[: cfg.max_sessions]
        by_session = {sid: by_session[sid] for sid in allowed_sessions}

    trimmed_turns: List[TurnRecord] = []
    for session_id, records in by_session.items():
        records.sort(key=lambda r: r.turn_index)
        if cfg.max_turns_per_session is not None:
            records = records[: cfg.max_turns_per_session]
        trimmed_turns.extend(records)

    trimmed_turns.sort(key=lambda r: (r.session_id, r.turn_index))
    return trimmed_turns


def _build_nodes_edges(turns: List[TurnRecord]) -> Tuple[List[Dict[str, object]], List[Dict[str, object]]]:
    nodes: List[Dict[str, object]] = []
    edges: List[Dict[str, object]] = []

    index_by_ref: Dict[Tuple[str, int], int] = {}
    for node_id, turn in enumerate(turns):
        index_by_ref[(turn.session_id, turn.turn_index)] = node_id
        nodes.append(
            {
                "id": node_id,
                "session_id": turn.session_id,
                "turn_index": turn.turn_index,
                "speaker": turn.speaker,
                "text": turn.text,
            }
        )

    step_counter = 0
    sessions: Dict[str, List[TurnRecord]] = {}
    for turn in turns:
        sessions.setdefault(turn.session_id, []).append(turn)

    for session_id, session_turns in sessions.items():
        session_turns.sort(key=lambda r: r.turn_index)
        for prev, curr in zip(session_turns, session_turns[1:]):
            src = index_by_ref[(prev.session_id, prev.turn_index)]
            dst = index_by_ref[(curr.session_id, curr.turn_index)]
            edges.append(
                {
                    "step": step_counter,
                    "src": src,
                    "dst": dst,
                    "val": 1,
                }
            )
            step_counter += 1

    return nodes, edges


def _token_count(text: str) -> int:
    return len([tok for tok in text.split() if tok])

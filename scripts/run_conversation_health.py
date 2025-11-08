#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Dict

from adapters.conversation.adapter import ConversationAdapter


def load_transcript(path: Path) -> List[Dict[str, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    # Support both {"turns": [...] } and {"transcript": [...]}
    turns = data.get("turns") or data.get("transcript") or []
    out = []
    for t in turns:
        speaker = t.get("speaker") or t.get("role") or "Speaker"
        text = t.get("text") or t.get("content") or ""
        if not text:
            continue
        out.append({"speaker": speaker, "text": text})
    return out


def role_for_index(idx: int) -> str:
    # Alternate roles to encourage adjacency-pair detection
    return "user" if idx % 2 == 0 else "assistant"


def process_file(path: Path, window: int) -> Dict:
    adapter = ConversationAdapter(window_size=window)
    turns = load_transcript(path)
    signals = []
    for i, turn in enumerate(turns):
        role = role_for_index(i)
        sig = adapter.process_turn(role=role, text=turn["text"])
        signals.append(sig.to_dict())
    # Summary
    summary = adapter.get_conversation_summary()
    # Include last 10 signals for inspection
    recent = adapter.get_recent_signals(min(10, len(adapter.turns)))
    summary["recent"] = [s.to_dict() for s in recent]
    return {"file": str(path), "summary": summary, "signals": signals}


def main() -> None:
    ap = argparse.ArgumentParser(description="Run conversation health metrics over cleaned transcripts")
    ap.add_argument("--input-dir", default="reports/conversation_clean")
    ap.add_argument("--out-dir", default="reports/conversation_metrics")
    ap.add_argument("--window", type=int, default=6, help="Sliding window size for analysis")
    args = ap.parse_args()

    in_dir = Path(args.input_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    files = list(in_dir.glob("*.json")) + list((in_dir / "Bad").glob("*.json"))
    results_index = []
    for fp in files:
        try:
            result = process_file(fp, args.window)
            out_file = out_dir / (fp.stem + ".metrics.json")
            out_file.write_text(json.dumps(result, indent=2), encoding="utf-8")
            results_index.append({
                "file": str(fp),
                "out": str(out_file),
                **result["summary"],
            })
            print(f"Analyzed {fp.name}")
        except Exception as e:
            print(f"Failed {fp}: {e}")

    (out_dir / "index.json").write_text(json.dumps(results_index, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

\n\n# DEPRECATED: use pipeline entry points\nimport warnings\nwarnings.warn('This script is deprecated; see docs/DEPRECATIONS.md', DeprecationWarning)\n

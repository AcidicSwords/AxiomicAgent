#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List


META_PATTERNS = [
    r"^\s*edited by\b.*$",
    r"^\s*transcript\b.*$",
    r"^\s*subscribe\b.*$",
    r"^\s*sign in\b.*$",
    r"^\s*copyright\b.*$",
    r"^\s*all rights reserved\b.*$",
    # Common web boilerplate seen in Medium and similar pages
    r"^\s*(get unlimited access|become a member)\b.*$",
    r"^\s*medium\b.*$",
]
META_RE = [re.compile(p, re.IGNORECASE) for p in META_PATTERNS]


def sentence_split(text: str) -> List[str]:
    # Simple sentence splitter; avoids splitting on single letters or common abbreviations
    text = text.strip()
    if not text:
        return []
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)
    # Split on . ! ? followed by space + capital or end of line
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\[\(\"'])", text)
    out = []
    for p in parts:
        p = p.strip()
        if len(p) >= 2:
            out.append(p)
    return out if out else [text]


def is_meta(line: str) -> bool:
    for rx in META_RE:
        if rx.match(line):
            return True
    return False


def parse_file(cleaned_json: Path, chunk_size: int = 1) -> Dict:
    data = json.loads(cleaned_json.read_text(encoding="utf-8"))
    title = data.get("title") or cleaned_json.stem
    transcript = data.get("transcript") or []
    turns: List[Dict[str, str]] = []
    for ex in transcript:
        speaker = (ex.get("speaker") or "Speaker").strip()
        text = (ex.get("text") or "").strip()
        if not text or is_meta(text):
            continue
        # Split into sentences; keep short ones if they are not pure fillers
        sents = sentence_split(text)
        if chunk_size <= 1:
            for s in sents:
                if len(s) < 2:
                    continue
                turns.append({"speaker": speaker, "text": s})
        else:
            for i in range(0, len(sents), chunk_size):
                chunk = " ".join(sents[i:i+chunk_size]).strip()
                if len(chunk) < 2:
                    continue
                turns.append({"speaker": speaker, "text": chunk})
    return {
        "source": str(cleaned_json),
        "title": title,
        "turns": turns,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Create parsed, turn-level conversation JSONs from cleaned transcripts")
    ap.add_argument("--input-dir", default="RAWDATA/ConversationClean")
    ap.add_argument("--out-dir", default="RAWDATA/ConversationParsed")
    ap.add_argument("--chunk-size", type=int, default=1, help="Number of sentences per turn (>=1)")
    args = ap.parse_args()

    in_dir = Path(args.input_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    files = list(in_dir.glob("*.json"))
    for fp in files:
        try:
            cs = max(1, int(getattr(args, "chunk_size", 1)))
            parsed = parse_file(fp, chunk_size=cs)
            out = out_dir / (fp.stem + "_parsed.json")
            out.write_text(json.dumps(parsed, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"Parsed: {fp.name} -> {out.name} (chunk={cs}, turns={len(parsed.get('turns') or [])})")
        except Exception as e:
            print(f"Failed {fp}: {e}")


if __name__ == "__main__":
    main()

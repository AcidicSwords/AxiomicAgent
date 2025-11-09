#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List

from pdfminer.high_level import extract_text


WEB_ARTIFACT_PATTERNS = [
    r"^\s*Subscribe\b.*$",
    r"^\s*Sign in\b.*$",
    r"^\s*Ac\s*\d{4}.*$",
    r"^\s*All rights reserved.*$",
    r"^\s*Page\s+\d+\s+of\s+\d+\s*$",
    r"^\s*The\s+On\s+Being\s+Project.*$",
    r"^\s*The\s+Singju\s+Post.*$",
    r"^\s*Medium.*$",
    r"^\s*\d{1,3}\s*$",
]
WEB_ARTIFACT_RE = [re.compile(p, re.IGNORECASE) for p in WEB_ARTIFACT_PATTERNS]


SPEAKER_LINE_RE = re.compile(r"^(?P<speaker>[A-Z][A-Z .\-\'\(\)]{1,60}|[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})\s*[:\-—]\s*(?P<text>.*)$")
TIMESTAMP_SPEAKER_RE = re.compile(r"^(?P<ts>\[?\d{1,2}:\d{2}(:\d{2})?\]?)\s*(?P<speaker>[A-Z][A-Za-z .\-\'\(\)]{1,60})\s*[:\-—]\s*(?P<text>.*)$")


def read_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        return extract_text(str(path))
    return path.read_text(encoding="utf-8", errors="ignore")


def clean_lines(text: str) -> List[str]:
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in text.splitlines()]
    out: List[str] = []
    for ln in lines:
        if not ln:
            continue
        # Normalize common punctuation/markdown
        ln = ln.replace("**", " ").replace("*", " ")
        ln = ln.replace("\u2014", " - ").replace("\u2013", " - ")  # em/en dash
        ln = ln.strip("- ")
        if any(rx.match(ln) for rx in WEB_ARTIFACT_RE):
            continue
        if re.search(r"https?://\S+", ln):
            continue
        out.append(ln)
    return out


def parse_transcript(lines: List[str]) -> Dict:
    exchanges: List[Dict[str, str]] = []
    actors: List[str] = []
    current_speaker = None
    buffer: List[str] = []

    def flush():
        nonlocal buffer, current_speaker
        if current_speaker is not None and buffer:
            exchanges.append({"speaker": current_speaker, "text": " ".join(buffer).strip()})
            buffer = []

    for ln in lines:
        m = TIMESTAMP_SPEAKER_RE.match(ln) or SPEAKER_LINE_RE.match(ln)
        if m:
            flush()
            sp = m.group("speaker").strip().rstrip(":")
            txt = m.group("text").strip()
            current_speaker = sp
            if sp not in actors:
                actors.append(sp)
            if txt:
                buffer.append(txt)
        else:
            if current_speaker is not None:
                buffer.append(ln)
            else:
                exchanges.append({"speaker": "NARRATION", "text": ln})
    flush()
    return {"actors": actors, "exchanges": exchanges}


def summarize_context(lines: List[str]) -> str:
    text = " ".join(lines[:20])
    parts = re.split(r"(?<=[.!?])\s+", text)
    return " ".join(parts[:2]).strip()


def scrub_file(path: Path) -> Dict:
    raw = read_text(path)
    lines = clean_lines(raw)
    parsed = parse_transcript(lines)
    context = summarize_context(lines)
    return {"source_file": str(path), "title": Path(path).stem, "actors": parsed["actors"], "context": context, "transcript": parsed["exchanges"]}


def write_outputs(data: Dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    base = Path(data["title"]).name
    (out_dir / f"{base}.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    with (out_dir / f"{base}.md").open("w", encoding="utf-8") as f:
        f.write(f"# {data['title']}\n\n")
        if data.get("context"):
            f.write(f"**Context:** {data['context']}\n\n")
        if data.get("actors"):
            f.write("**Actors:** " + ", ".join(data["actors"]) + "\n\n")
        for ex in data.get("transcript", []):
            sp = ex.get("speaker"); tx = ex.get("text")
            f.write(f"**{sp}:** {tx}\n\n")


def main() -> None:
    ap = argparse.ArgumentParser(description="Scrub conversation PDFs/TXT to clean transcripts")
    ap.add_argument("--input-dir", default="RawConversation")
    # Clean transcripts are intermediate artifacts → keep under RAWDATA
    ap.add_argument("--out-dir", default="RAWDATA/ConversationClean")
    args = ap.parse_args()

    in_dir = Path(args.input_dir)
    out_dir = Path(args.out_dir)
    found = list(in_dir.glob("*.pdf")) + list(in_dir.glob("*.txt"))
    if not found:
        raise SystemExit(f"No files found in {in_dir}")
    for fp in found:
        try:
            data = scrub_file(fp)
            write_outputs(data, out_dir)
            print(f"Scrubbed: {fp.name}")
        except Exception as e:
            print(f"Failed to scrub {fp}: {e}")


if __name__ == "__main__":
    main()

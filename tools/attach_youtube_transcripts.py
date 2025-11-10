#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Dict, Any, List


def _fetch_transcript(video_id: str) -> Dict[str, Any] | None:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi  # type: ignore
    except Exception as e:
        print("[attach] youtube_transcript_api not available:", e)
        return None
    try:
        raw = YouTubeTranscriptApi.get_transcript(video_id)
    except Exception as e:
        print(f"[attach] transcript fetch failed for {video_id}: {e}")
        return None
    segments: List[dict] = []
    for seg in raw or []:
        try:
            start = float(seg.get("start", 0.0))
            end = start + float(seg.get("duration", 0.0))
            text = str(seg.get("text", "")).strip()
        except Exception:
            continue
        if text:
            segments.append({"start": start, "end": end, "text": text})
    return {"video_id": video_id, "segments": segments}


def main() -> None:
    ap = argparse.ArgumentParser(description="Attach YouTube transcripts to a normalized playlist JSON.")
    ap.add_argument("--input-json", required=True)
    ap.add_argument("--out-json")
    ap.add_argument("--out-dir", default="RAWDATA/RawYTTranscripts")
    args = ap.parse_args()

    in_path = Path(args.input_json)
    data = json.loads(in_path.read_text(encoding="utf-8"))
    course_id = data.get("course_id") or in_path.stem
    items: List[Dict[str, Any]] = data.get("items", [])

    out_root = Path(args.out_dir) / course_id
    out_root.mkdir(parents=True, exist_ok=True)

    changed = False
    for item in items:
        vid = str(item.get("item_id") or "").strip()
        if not vid or item.get("transcript_path"):
            continue
        transcript = _fetch_transcript(vid)
        if not transcript or not transcript.get("segments"):
            continue
        out_fp = out_root / f"{vid}.json"
        out_fp.write_text(json.dumps(transcript, indent=2), encoding="utf-8")
        rel = os.path.relpath(out_fp, start=in_path.parent)
        item["transcript_path"] = rel.replace("\\", "/")
        changed = True

    if changed:
        out_path = Path(args.out_json) if args.out_json else in_path
        out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        print(f"[attach] Updated normalized JSON with transcripts: {out_path}")
    else:
        print("[attach] No transcripts attached (none found or already present)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.transcripts import from_youtube_transcript_api, parse_vtt_to_segments
import subprocess


def _run(cmd: list[str]) -> tuple[int, str, str]:
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = proc.communicate()
    return proc.returncode or 0, out, err


def try_fetch_transcript_api(video_id: str):
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        raw = YouTubeTranscriptApi.get_transcript(video_id, languages=["en", "en-US"])  # type: ignore
        return from_youtube_transcript_api(video_id, raw)
    except Exception:
        return None


def try_fetch_transcript_autosub(video_id: str, subs_dir: Path):
    subs_dir.mkdir(parents=True, exist_ok=True)
    out_template = str((subs_dir / f"{video_id}.%(ext)s").resolve())
    cmd = [
        "yt-dlp",
        "--skip-download",
        "--write-auto-sub",
        "--sub-lang",
        "en",
        "--sub-format",
        "vtt",
        "-o",
        out_template,
        f"https://www.youtube.com/watch?v={video_id}",
    ]
    code, out, err = _run(cmd)
    vtt_path = subs_dir / f"{video_id}.en.vtt"
    if vtt_path.exists():
        return parse_vtt_to_segments(video_id, vtt_path)
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description="Fetch transcripts for an existing normalized YouTube course JSON.")
    ap.add_argument("--input-json", required=True, help="Path to normalized JSON (items list).")
    ap.add_argument("--output-dir", required=True, help="Directory to write normalized.json and transcripts/")
    args = ap.parse_args()

    input_path = Path(args.input_json)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    subs_dir = out_dir / "subs_raw"
    transcripts_dir = out_dir / "transcripts"
    transcripts_dir.mkdir(parents=True, exist_ok=True)

    data = json.loads(input_path.read_text(encoding="utf-8"))
    # Normalize shape differences (file may be plain normalized or builder-ready)
    course_id = data.get("course_id") or input_path.stem
    items = data.get("items") or []
    if not items and isinstance(data, dict) and data.get("entries"):
        # Treat as raw yt-dlp dump; this path is not ideal, but we can still map
        print("Input appears to be raw dump; please run normalize_youtube_playlist.py first.")
        sys.exit(2)

    for it in items:
        vid = str(it.get("item_id") or it.get("video_id") or "").strip()
        if not vid:
            continue
        transcript = try_fetch_transcript_api(vid)
        if transcript is None:
            transcript = try_fetch_transcript_autosub(vid, subs_dir)
        if transcript and transcript.get("segments"):
            out_path = transcripts_dir / f"{vid}.json"
            out_path.write_text(json.dumps(transcript, ensure_ascii=False, indent=2), encoding="utf-8")
            it["has_transcript"] = True
            it["transcript_path"] = (Path("transcripts") / f"{vid}.json").as_posix()
        else:
            it["has_transcript"] = False
            it["transcript_path"] = None

    normalized = dict(data)
    normalized["course_id"] = course_id
    out_norm = out_dir / "normalized.json"
    out_norm.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote normalized + transcripts to {out_norm}")


if __name__ == "__main__":
    main()


#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from builders.curriculum.youtube_series import normalize_playlist_payload
from core.transcripts import (
    coarse_segments,
    from_youtube_transcript_api,
    parse_vtt_to_segments,
)


def _run(cmd: list[str]) -> tuple[int, str, str]:
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = proc.communicate()
    return proc.returncode or 0, out, err


def fetch_playlist_json(playlist_url_or_id: str) -> dict:
    # Use yt-dlp to dump playlist metadata (flat playlist is fine)
    cmd = [
        "yt-dlp",
        "--dump-single-json",
        "--flat-playlist",
        playlist_url_or_id,
    ]
    code, out, err = _run(cmd)
    if code != 0 or not out.strip():
        raise RuntimeError(f"yt-dlp failed ({code}): {err.strip()}")
    return json.loads(out)


def try_fetch_transcript_api(video_id: str):
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        raw = YouTubeTranscriptApi.get_transcript(video_id, languages=["en", "en-US"])  # type: ignore
        return from_youtube_transcript_api(video_id, raw)
    except Exception:
        return None


def try_fetch_transcript_autosub(video_id: str, subs_dir: Path):
    subs_dir.mkdir(parents=True, exist_ok=True)
    # Ask yt-dlp to write auto-generated subtitles (WebVTT)
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
    # Expected file: <video_id>.en.vtt
    vtt_path = subs_dir / f"{video_id}.en.vtt"
    if vtt_path.exists():
        return parse_vtt_to_segments(video_id, vtt_path)
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect YouTube playlist + transcripts and normalize.")
    parser.add_argument("--playlist", required=True, help="YouTube playlist URL or ID")
    parser.add_argument("--course-id", required=True, help="Course id to embed in normalized output")
    parser.add_argument("--output-dir", required=True, help="Directory to write normalized.json and transcripts/")
    parser.add_argument("--title", help="Optional course title override")
    parser.add_argument("--profile", default="youtube_series", help="Profile hint (youtube_series/crashcourse/3b1b)")
    parser.add_argument("--videos-per-step", type=int, default=1, help="Number of videos per step (default 1)")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    subs_dir = out_dir / "subs_raw"
    transcripts_dir = out_dir / "transcripts"
    transcripts_dir.mkdir(parents=True, exist_ok=True)

    # 1) Fetch playlist
    payload = fetch_playlist_json(args.playlist)
    normalized = normalize_playlist_payload(
        payload,
        course_id=args.course_id,
        title=args.title,
        profile=args.profile,
        videos_per_step=args.videos_per_step,
    )

    # 2) Try transcripts per video
    # Build quick lookup by id for augmentation later
    items = normalized.get("items", [])
    by_id = {str(it.get("item_id")): it for it in items}
    for item in items:
        vid = str(item.get("item_id"))
        transcript = try_fetch_transcript_api(vid)
        if transcript is None:
            transcript = try_fetch_transcript_autosub(vid, subs_dir)
        if transcript and transcript.get("segments"):
            # Optionally compress to coarse segments for sanity check
            # but store full transcript; builder will coarse later.
            out_path = transcripts_dir / f"{vid}.json"
            out_path.write_text(json.dumps(transcript, ensure_ascii=False, indent=2), encoding="utf-8")
            rel_path = Path("transcripts") / f"{vid}.json"
            item["has_transcript"] = True
            item["transcript_path"] = rel_path.as_posix()
        else:
            item["has_transcript"] = False
            item["transcript_path"] = None

    # 3) Write normalized JSON
    normalized_path = out_dir / "normalized.json"
    normalized_path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote normalized playlist + transcripts to {normalized_path}")


if __name__ == "__main__":
    main()


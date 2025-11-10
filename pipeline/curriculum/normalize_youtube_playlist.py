#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

CHANNEL_FAMILIES = {
    "3blue1brown": "youtube_3b1b",
    "3b1b": "youtube_3b1b",
    "crashcourse": "youtube_crashcourse",
    "crash course": "youtube_crashcourse",
}

QUIZ_KEYWORDS = ("quiz", "test", "exam", "practice")
PROJECT_KEYWORDS = ("project", "demo", "build", "challenge", "exercise")
READING_KEYWORDS = ("reading", "book", "article", "essay")
INTRO_KEYWORDS = ("introduction", "overview", "welcome")


def normalize_playlist_payload(
    raw_payload: Dict[str, Any],
    *,
    course_id: Optional[str] = None,
    title: Optional[str] = None,
    profile: Optional[str] = None,
    videos_per_step: int = 1,
) -> Dict[str, Any]:
    playlist_id = raw_payload.get("playlist_id") or raw_payload.get("id") or course_id
    if not playlist_id:
        raise ValueError("playlist payload missing playlist_id")
    course_title = title or raw_payload.get("title") or playlist_id
    channel_title = (raw_payload.get("channel_title") or "")
    normalized_profile = profile or CHANNEL_FAMILIES.get(channel_title.lower(), "youtube_series")
    videos_per_step = max(1, int(videos_per_step))
    entries = raw_payload.get("entries") or raw_payload.get("videos") or []
    items: List[Dict[str, Any]] = []
    for idx, entry in enumerate(entries, start=1):
        video_id = entry.get("id") or entry.get("video_id")
        if not video_id:
            continue
        video_title = entry.get("title") or f"Video {idx}"
        description = entry.get("description") or ""
        playlist_index = entry.get("playlist_index") or idx
        order = int(playlist_index) - 1
        if order < 0:
            order = idx - 1
        step_index = order // videos_per_step
        week = step_index + 1
        kind = _classify_video_kind(video_title, description)
        tags = _collect_tags(video_title, description, channel_title)
        metrics = {
            "views": entry.get("view_count", 0),
            "likes": entry.get("like_count", 0),
            "duration": entry.get("duration", 0),
        }
        items.append(
            {
                "item_id": video_id,
                "title": video_title,
                "description": description,
                "kind": kind,
                "week": week,
                "order": order,
                "step_index": step_index,
                "tags": sorted(tags),
                "metrics": metrics,
                "source_path": entry.get("webpage_url") or f"https://youtu.be/{video_id}",
            }
        )
    return {
        "course_id": course_id or playlist_id,
        "title": course_title,
        "profile": normalized_profile,
        "channel_title": channel_title,
        "videos_per_step": videos_per_step,
        "items": items,
    }


def _classify_video_kind(title: str, description: str) -> str:
    text = f"{title} {description}".lower()
    if any(keyword in text for keyword in QUIZ_KEYWORDS):
        return "assessment"
    if any(keyword in text for keyword in PROJECT_KEYWORDS):
        return "project"
    if any(keyword in text for keyword in READING_KEYWORDS):
        return "reading"
    if any(keyword in text for keyword in INTRO_KEYWORDS):
        return "concept"
    return "lecture"


def _collect_tags(title: str, description: str, channel_title: str) -> List[str]:
    tags = set()
    if channel_title:
        tags.add(channel_title.lower().replace(" ", ""))
    text = f"{title} {description}".lower()
    if "calculus" in text or "derivative" in text:
        tags.add("math")
    if "history" in text or "ancient" in text:
        tags.add("history")
    if "physics" in text or "quantum" in text:
        tags.add("physics")
    if "computer" in text or "algorithm" in text:
        tags.add("computer_science")
    if "chemistry" in text:
        tags.add("chemistry")
    return list(tags)


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize YouTube playlist JSON into curriculum schema.")
    parser.add_argument("--input", required=True, help="Path to raw playlist JSON (yt-dlp or API output).")
    parser.add_argument("--output", required=True, help="Path to write normalized JSON.")
    parser.add_argument("--course-id", help="Override course_id (defaults to playlist_id).")
    parser.add_argument("--title", help="Override title.")
    parser.add_argument("--profile", help="Override profile (youtube_series, youtube_crashcourse, ...).")
    parser.add_argument("--videos-per-step", type=int, default=1, help="Videos per step (default 1).")
    args = parser.parse_args()
    raw_bytes = Path(args.input).read_bytes()
    text = None
    for encoding in ("utf-8", "utf-8-sig", "utf-16", "utf-16-le", "utf-16-be"):
        try:
            text = raw_bytes.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise UnicodeDecodeError("normalize_youtube_playlist", b"", 0, 1, "Unable to decode input file")
    payload = json.loads(text)
    normalized = normalize_playlist_payload(
        payload,
        course_id=args.course_id,
        title=args.title,
        profile=args.profile,
        videos_per_step=args.videos_per_step,
    )
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(normalized, indent=2), encoding="utf-8")
    print(f"Wrote normalized playlist to {output_path}")


if __name__ == "__main__":
    main()

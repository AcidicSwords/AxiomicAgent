#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

from builders.curriculum.youtube_series import normalize_playlist_payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize YouTube playlist JSON into curriculum items.")
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

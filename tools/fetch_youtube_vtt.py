#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Dict, Any, List


def _run(cmd: List[str]) -> int:
    try:
        print("$", " ".join(cmd), flush=True)
        return subprocess.call(cmd)
    except FileNotFoundError:
        return 127


def main() -> None:
    ap = argparse.ArgumentParser(description="Fetch YouTube auto-captions (VTT) and attach transcript_path.")
    ap.add_argument("--input-json", required=True, help="Normalized playlist JSON path")
    ap.add_argument("--out-json", help="Output normalized JSON (default: overwrite input)")
    ap.add_argument("--out-dir", default="RAWDATA/RawYTTranscripts", help="Directory to store VTT files per course")
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
        rc = _run([
            "yt-dlp",
            "--skip-download",
            "--write-auto-sub",
            "--sub-lang",
            "en,live_chat",
            "--convert-subs",
            "vtt",
            "-o",
            str(out_root / "%(_id)s.%(ext)s").replace("%(_id)s", "%(id)s"),
            f"https://youtu.be/{vid}",
        ])
        if rc != 0:
            continue
        vtts = list(out_root.glob(f"{vid}*.vtt"))
        if not vtts:
            continue
        vtt_path = vtts[0]
        final = out_root / f"{vid}.vtt"
        if vtt_path != final:
            try:
                vtt_path.replace(final)
            except Exception:
                final = vtt_path
        rel = os.path.relpath(final, start=in_path.parent)
        item["transcript_path"] = rel.replace("\\", "/")
        changed = True

    if changed:
        out_path = Path(args.out_json) if args.out_json else in_path
        out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        print(f"[vtt] Updated normalized JSON with transcript_path: {out_path}")
    else:
        print("[vtt] No transcripts attached (none found or already present)")


if __name__ == "__main__":
    main()

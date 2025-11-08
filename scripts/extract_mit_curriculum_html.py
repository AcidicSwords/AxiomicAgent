#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from builders.curriculum.mit_ocw import extract_and_write, extract_items_from_zip


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract normalized MIT curriculum JSON from raw OCW zips."
    )
    parser.add_argument(
        "--raw-root",
        default="RawOCW",
        help="Directory containing MIT OCW course zip archives.",
    )
    parser.add_argument(
        "--output-dir",
        default="datasets/raw_mit_curriculum",
        help="Output directory for normalized JSON.",
    )
    parser.add_argument(
        "--profile",
        default="stem",
        choices=["stem", "psych_humanities", "lit_essay"],
        help="Curriculum profile to apply while extracting.",
    )
    parser.add_argument(
        "--course-zip",
        help="Optional path to a single course zip to extract (overrides --raw-root).",
    )
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.course_zip:
        zip_path = Path(args.course_zip)
        if not zip_path.exists():
            raise SystemExit(f"{zip_path} does not exist")
        course = extract_items_from_zip(zip_path, profile=args.profile)
        out_path = out_dir / f"{zip_path.stem}.json"
        out_path.write_text(json.dumps(course, indent=2), encoding="utf-8")
        print(f"Extracted {zip_path.name} -> {out_path}")
    else:
        raw_root = Path(args.raw_root)
        extract_and_write(raw_root, out_dir, profile=args.profile)

    print("Done.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from builders.curriculum import CurriculumBuilderParams, build_from_items_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Build YouTube curriculum dataset from normalized JSON.")
    parser.add_argument("--input-json", required=True, help="Normalized playlist JSON path.")
    parser.add_argument("--output-zip", required=True, help="Destination dataset zip.")
    parser.add_argument("--profile", default="youtube_series", help="Curriculum profile to apply.")
    parser.add_argument(
        "--step-semantics",
        default="week",
        choices=["week", "section_chunk", "static"],
        help="How to assign step ids.",
    )
    args = parser.parse_args()

    input_path = Path(args.input_json)
    output_path = Path(args.output_zip)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    params = CurriculumBuilderParams(step_semantics=args.step_semantics, profile=args.profile)
    build_from_items_json(input_path, output_path, params=params)
    print(f"Wrote YouTube curriculum dataset to {output_path}")


if __name__ == "__main__":
    main()
\n\n# DEPRECATED: use pipeline entry points\nimport warnings\nwarnings.warn('This script is deprecated; see docs/DEPRECATIONS.md', DeprecationWarning)\n

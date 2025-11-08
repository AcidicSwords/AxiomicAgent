#!/usr/bin/env python
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from builders.curriculum import CurriculumBuilderParams, build_from_items_json

PROFILE_OVERRIDES = {
    "9.00sc-fall-2011": ("psych_humanities", "week"),
    "21w.735-fall-2004": ("lit_essay", "week"),
    "21l.002-spring-2010": ("lit_essay", "week"),
    "21h.102-spring-2018": ("psych_humanities", "week"),
}


def build_dataset_from_json(
    raw_path: Path, out_zip: Path, params: CurriculumBuilderParams
) -> None:
    build_from_items_json(raw_path, out_zip, params)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build curriculum datasets from normalized MIT JSON."
    )
    parser.add_argument(
        "--raw-dir",
        default="datasets/raw_mit_curriculum",
        help="Directory of normalized JSON files.",
    )
    parser.add_argument(
        "--out-dir",
        default="datasets/mit_curriculum_datasets",
        help="Directory to write dataset zips.",
    )
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    json_paths = sorted(raw_dir.glob("*.json"))
    if not json_paths:
        raise SystemExit(f"No normalized curriculum JSON found in {raw_dir}")

    for json_path in json_paths:
        out_zip = out_dir / f"{json_path.stem}.zip"
        profile, step_semantics = PROFILE_OVERRIDES.get(
            json_path.stem, ("stem", "section_chunk")
        )
        params = CurriculumBuilderParams(
            step_semantics=step_semantics, profile=profile
        )
        print(
            f"Building dataset for {json_path.stem} -> {out_zip} "
            f"(profile={profile}, step_semantics={step_semantics})"
        )
        build_dataset_from_json(json_path, out_zip, params)

    print("Done.")


if __name__ == "__main__":
    main()

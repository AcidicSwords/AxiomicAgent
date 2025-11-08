#!/usr/bin/env python
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def run(cmd: list[str]) -> None:
    print("$", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> None:
    ap = argparse.ArgumentParser(description="End-to-end curriculum pipeline (zipless runtime)")
    ap.add_argument("--zip-dir", default="datasets/mit_curriculum_datasets")
    ap.add_argument("--fs-dir", default="datasets/mit_curriculum_fs")
    ap.add_argument("--insights-out", default="reports/mit_curriculum_insights_fs")
    ap.add_argument("--dynamics-out", default="reports/mit_curriculum_dynamics_fs")
    ap.add_argument("--rebuild", action="store_true", help="Rebuild datasets before running")
    ap.add_argument("--heads", nargs="*", default=["monte_carlo","forecast","regime_change"]) 
    args = ap.parse_args()

    zip_dir = Path(args.zip_dir)
    fs_dir = Path(args.fs_dir)
    insights_out = Path(args.insights_out)
    dynamics_out = Path(args.dynamics_out)

    if args.rebuild:
        # Rebuild MIT datasets (uses existing script)
        run(["python","-m","scripts.build_mit_curriculum_datasets"])  # builds into zip_dir
        # Optionally rebuild YouTube if configs present; ignore failures
        try:
            run(["python","-m","scripts.build_youtube_curriculum"])  # expects its own args/config
        except Exception:
            print("[warn] build_youtube_curriculum failed or not configured; continuing")

    # Run zipless insights
    run([
        "python","-m","scripts.run_mit_curriculum_zipless",
        "--zip-dir", str(zip_dir),
        "--fs-dir", str(fs_dir),
        "--out-dir", str(insights_out),
        "--compute-spread","--compute-locality",
        "--heads", *args.heads,
        "--reporter","insight",
    ])

    # Run zipless dynamics
    run([
        "python","-m","scripts.run_mit_curriculum_zipless",
        "--zip-dir", str(zip_dir),
        "--fs-dir", str(fs_dir),
        "--out-dir", str(dynamics_out),
        "--compute-spread","--compute-locality",
        "--heads", *args.heads,
        "--reporter","curriculum_dynamics",
    ])


if __name__ == "__main__":
    main()

\n\n# DEPRECATED: use pipeline entry points\nimport warnings\nwarnings.warn('This script is deprecated; see docs/DEPRECATIONS.md', DeprecationWarning)\n

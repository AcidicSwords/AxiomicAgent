#!/usr/bin/env python
from __future__ import annotations

import argparse
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


def run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr)
        raise SystemExit(f"Command failed: {' '.join(cmd)}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Archive old reports and regenerate full analysis")
    ap.add_argument("--datasets-dir", default="datasets/mit_curriculum_datasets")
    ap.add_argument("--archive", action="store_true", help="Archive existing reports/yt_* before regenerating")
    args = ap.parse_args()

    reports = Path("reports")
    reports.mkdir(exist_ok=True)

    # 1) Archive if requested
    prev_ins = reports / "yt_insights"
    prev_dyn = reports / "yt_dynamics"
    arch_dir = None
    if args.archive and (prev_ins.exists() or prev_dyn.exists()):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        arch_dir = reports / f"archive_{ts}"
        arch_dir.mkdir(parents=True, exist_ok=True)
        if prev_ins.exists():
            shutil.move(str(prev_ins), str(arch_dir / "yt_insights"))
        if prev_dyn.exists():
            shutil.move(str(prev_dyn), str(arch_dir / "yt_dynamics"))
        print(f"Archived previous reports to {arch_dir}")

    # 2) Regenerate insights/dynamics into default folders
    out_ins = reports / "yt_insights"
    out_dyn = reports / "yt_dynamics"
    out_ins.mkdir(parents=True, exist_ok=True)
    out_dyn.mkdir(parents=True, exist_ok=True)

    run([
        "python", "-m", "scripts.run_mit_curriculum_showcase",
        "--datasets-dir", args.datasets_dir,
        "--out-dir", str(out_ins),
        "--compute-spread", "--compute-locality",
        "--heads", "monte_carlo", "forecast", "regime_change",
        "--reporter", "insight",
    ])

    run([
        "python", "-m", "scripts.run_mit_curriculum_showcase",
        "--datasets-dir", args.datasets_dir,
        "--out-dir", str(out_dyn),
        "--compute-spread", "--compute-locality",
        "--heads", "monte_carlo", "forecast", "regime_change",
        "--reporter", "curriculum_dynamics",
    ])

    # 3) Export CSV + dashboards + pivots
    run([
        "python", "-m", "scripts.export_curriculum_metrics",
        "--insights-dir", str(out_ins),
        "--dynamics-dir", str(out_dyn),
        "--out", str(reports / "comparisons" / "curriculum_summary.csv"),
    ])
    run([
        "python", "-m", "scripts.export_curriculum_dashboard",
        "--csv", str(reports / "comparisons" / "curriculum_summary.csv"),
        "--out-md", str(reports / "comparisons" / "curriculum_summary.md"),
        "--out-html", str(reports / "comparisons" / "curriculum_summary.html"),
    ])
    run([
        "python", "-m", "scripts.export_top_pivots",
        "--dynamics-dir", str(out_dyn),
        "--out-json", str(reports / "comparisons" / "top_pivots.json"),
        "--out-md", str(reports / "comparisons" / "top_pivots.md"),
        "--top-n", "3",
    ])

    # 4) Compare new vs previous if archived
    if arch_dir and (arch_dir / "yt_insights").exists() and (arch_dir / "yt_dynamics").exists():
        run([
            "python", "-m", "scripts.compare_reports",
            "--prev-insights", str(arch_dir / "yt_insights"),
            "--prev-dynamics", str(arch_dir / "yt_dynamics"),
            "--new-insights", str(out_ins),
            "--new-dynamics", str(out_dyn),
            "--out-json", str(reports / "comparisons" / "compare_v2.json"),
            "--out-md", str(reports / "comparisons" / "compare_v2.md"),
        ])

    print("All reports generated.")


if __name__ == "__main__":
    main()


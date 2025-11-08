#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path
from typing import Any, Dict

import adapters  # noqa: F401
import reporters  # noqa: F401

from core.engine import Engine
from core.policy import CapacityPolicy, IdentityPolicy, PolicyConfig
from core.signals import DefaultSignalComputer, SignalConfig


REQUIRED_FILES = {"nodes.csv", "edges_obs.csv"}
OPTIONAL_FILES = {"edges_true.csv", "meta.json"}


def extract_zip_to_dir(zip_path: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = set(zf.namelist())
        for fname in REQUIRED_FILES | OPTIONAL_FILES:
            if fname in names:
                zf.extract(fname, path=out_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run engine on curriculum datasets (zipless FS provider)")
    parser.add_argument("--zip-dir", default="datasets/mit_curriculum_datasets", help="Directory with dataset zips")
    parser.add_argument("--fs-dir", default="datasets/mit_curriculum_fs", help="Output directory for extracted datasets")
    parser.add_argument("--out-dir", default="reports/mit_curriculum_insights_fs", help="Directory for generated reports")
    parser.add_argument("--policy", choices=["identity", "capacity"], default="capacity")
    parser.add_argument("--max-edges", type=int, default=400)
    parser.add_argument("--sticky-fraction", type=float, default=0.5)
    parser.add_argument("--compute-spread", action="store_true")
    parser.add_argument("--compute-locality", action="store_true")
    parser.add_argument("--reporter", default="insight", help="Reporter to use (insight, curriculum_dynamics, ...)")
    parser.add_argument("--heads", nargs="*", default=[], help="Optional signal heads to enable")
    parser.add_argument("--monte-carlo-samples", type=int, default=16)
    parser.add_argument("--monte-carlo-dropout", type=float, default=0.1)
    parser.add_argument("--monte-carlo-jitter", type=float, default=0.1)
    parser.add_argument("--forecast-window", type=int, default=3)
    parser.add_argument("--regime-window", type=int, default=3)
    parser.add_argument("--regime-threshold", type=float, default=0.25)
    args = parser.parse_args()

    zip_dir = Path(args.zip_dir)
    fs_dir = Path(args.fs_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    zip_paths = sorted(zip_dir.glob("*.zip"))
    if not zip_paths:
        raise SystemExit(f"No datasets found in {zip_dir}")

    policy = (
        IdentityPolicy() if args.policy == "identity" else CapacityPolicy(PolicyConfig(max_edges=args.max_edges, sticky_fraction=args.sticky_fraction))
    )
    signal_config = SignalConfig(compute_spread=args.compute_spread, compute_locality=args.compute_locality)

    summary = []
    for zip_path in zip_paths:
        course_id = zip_path.stem
        course_dir = fs_dir / course_id
        if not (course_dir / "nodes.csv").exists() or not (course_dir / "edges_obs.csv").exists():
            extract_zip_to_dir(zip_path, course_dir)

        suffix = "insight" if args.reporter == "insight" else args.reporter
        report_path = out_dir / f"{course_id}_{suffix}.json"
        print(f"\n=== {course_id} (zipless) ===")
        print(f"dataset: {course_dir}")
        print(f"report:  {report_path}")

        core_cfg: Dict[str, Any] = {"capacity": {"max_edges": getattr(policy.config, "max_edges", None)}}
        if args.heads:
            core_cfg["heads"] = args.heads
            if "monte_carlo" in args.heads:
                core_cfg["monte_carlo"] = {"num_samples": args.monte_carlo_samples, "edge_dropout": args.monte_carlo_dropout, "weight_jitter": args.monte_carlo_jitter}
            if "forecast" in args.heads:
                core_cfg["forecast"] = {"window_size": args.forecast_window}
            if "regime_change" in args.heads:
                core_cfg["regime_change"] = {"window": args.regime_window, "threshold": args.regime_threshold}

        engine = Engine(
            adapter="curriculum_stream",
            dataset_path=str(course_dir),
            reporter=args.reporter,
            reporter_kwargs={"domain": "curriculum", "path": str(report_path)},
            core_config=core_cfg,
            policy=policy,
            signal_computer=DefaultSignalComputer(signal_config),
        )
        engine.run()

        report = json.loads(report_path.read_text(encoding="utf-8"))
        aggregates = report.get("aggregates", {})
        steps = report.get("steps", [])
        def _avg_from_steps(key: str):
            vals = [s.get(key) for s in steps if isinstance(s.get(key), (int, float))]
            return round(sum(vals)/len(vals), 3) if vals else None

        avg_q = aggregates.get("avg_q") or _avg_from_steps("q") or _avg_from_steps("mean_q")
        avg_ted = aggregates.get("avg_ted") or _avg_from_steps("ted") or _avg_from_steps("mean_ted")
        avg_stability = aggregates.get("avg_stability") or _avg_from_steps("s") or _avg_from_steps("stability")
        avg_spread = aggregates.get("avg_spread") or _avg_from_steps("spread")
        avg_continuity = _avg_from_steps("continuity")
        ted_tr_vals = [s.get("ted_trusted") for s in steps if isinstance(s.get("ted_trusted"), (int, float))]
        avg_ted_trusted = round(sum(ted_tr_vals)/len(ted_tr_vals), 3) if ted_tr_vals else aggregates.get("avg_ted_trusted")
        summary.append({"course_id": course_id, "avg_q": avg_q, "avg_ted": avg_ted, "avg_stability": avg_stability, "avg_spread": avg_spread, "avg_continuity": avg_continuity, "avg_ted_trusted": avg_ted_trusted})

    comparison_path = out_dir / "comparison.json"
    comparison_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nWrote comparison summary to {comparison_path}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import adapters  # noqa: F401
import reporters  # noqa: F401
from core.engine import Engine
from core.policy import CapacityPolicy, PolicyConfig
from core.signals import DefaultSignalComputer, SignalConfig

def run_one(course_dir: Path, out_path: Path, enable_features: bool, scales: Tuple[float, float, float]) -> Dict[str, float]:
    course_id = course_dir.name
    if enable_features:
        os.environ["AXIOM_RESOURCE_FEATURE_COURSES"] = course_id
    else:
        os.environ.pop("AXIOM_RESOURCE_FEATURE_COURSES", None)
    os.environ.pop("AXIOM_RESOURCE_FEATURE_TEST", None)
    g, r, l = scales
    os.environ["AXIOM_WEIGHT_SCALE"] = str(g)
    os.environ["AXIOM_RESOURCE_W_SCALE"] = str(r)
    os.environ["AXIOM_LECTURE_W_SCALE"] = str(l)
    os.environ["AXIOM_PSET_W_SCALE"] = "1.0"

    policy = CapacityPolicy(PolicyConfig(max_edges=400, sticky_fraction=0.5))
    eng = Engine(
        adapter="curriculum_stream",
        dataset_path=str(course_dir),
        reporter="insight",
        reporter_kwargs={"domain": "curriculum", "path": str(out_path)},
        policy=policy,
        signal_computer=DefaultSignalComputer(SignalConfig(compute_spread=True, compute_locality=True)),
    )
    eng.run()
    data = json.loads(out_path.read_text(encoding="utf-8"))
    agg = data.get("aggregates", {})
    return {
        "avg_q": float(agg.get("avg_q") or 0.0),
        "avg_ted": float(agg.get("avg_ted") or 0.0),
        "steps": int(agg.get("steps") or (len(data.get("steps") or []))),
    }

def main() -> None:
    zipless_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "datasets/mit_curriculum_fs")
    out_dir = Path(sys.argv[2] if len(sys.argv) > 2 else "reports/mit_curriculum_sweep")
    out_dir.mkdir(parents=True, exist_ok=True)

    courses = sorted(p for p in zipless_dir.iterdir() if p.is_dir())
    allow_csv = os.environ.get("AXIOM_SWEEP_COURSES")
    if allow_csv:
        allow = {c.strip() for c in allow_csv.split(",") if c.strip()}
        courses = [p for p in courses if p.name in allow]
    else:
        import re as _re
        courses = [p for p in courses if _re.match(r'^\d', p.name) or p.name.startswith("mit_")]
    scales = [
        (1.0, 1.0, 1.0),
        (1.0, 1.25, 1.1),
        (1.0, 1.5, 1.25),
        (1.0, 2.0, 1.5),
        (1.0, 2.5, 1.75),
        (1.0, 3.0, 2.0),
    ]

    summary: Dict[str, Dict[str, object]] = {}
    for course in courses:
        course_id = course.name
        base_path = out_dir / f"{course_id}_baseline.json"
        base = run_one(course, base_path, enable_features=False, scales=(1.0, 1.0, 1.0))
        rows: List[Dict[str, object]] = [{"scale": (0.0, 0.0, 0.0), **base}]

        for sc in scales:
            outp = out_dir / f"{course_id}_g{sc[0]}_r{sc[1]}_l{sc[2]}.json"
            res = run_one(course, outp, enable_features=True, scales=sc)
            rows.append({"scale": sc, **res})

        base_q = base["avg_q"]
        if base_q >= 0.85:
            best = max((r for r in rows[1:] if (base_q - r["avg_q"]) <= 0.02), key=lambda r: r["avg_q"], default=rows[0])
        else:
            candidates = [r for r in rows[1:] if r["avg_q"] >= 0.75]
            best = min(candidates, key=lambda r: sum(r["scale"]), default=max(rows[1:], key=lambda r: r["avg_q"]))

        summary[course_id] = {
            "baseline": base,
            "rows": rows,
            "recommended": best,
        }

    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(str(out_dir / "summary.json"))

if __name__ == "__main__":
    main()

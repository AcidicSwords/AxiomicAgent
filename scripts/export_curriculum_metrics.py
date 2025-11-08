#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, Any


def load_insight_comparison(insights_dir: Path) -> Dict[str, Dict[str, Any]]:
    cmp_path = insights_dir / "comparison.json"
    data = json.loads(cmp_path.read_text(encoding="utf-8"))
    out: Dict[str, Dict[str, Any]] = {}
    for row in data:
        out[str(row.get("course_id"))] = {
            "avg_q": row.get("avg_q"),
            "avg_TED": row.get("avg_ted"),
            "avg_spread": row.get("avg_spread"),
            "avg_continuity": row.get("avg_continuity"),
            "avg_ted_trusted": row.get("avg_ted_trusted"),
        }
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Export consolidated curriculum metrics to CSV")
    ap.add_argument("--insights-dir", default="reports/yt_insights", help="Directory with *_insight.json + comparison.json")
    ap.add_argument("--dynamics-dir", default="reports/yt_dynamics", help="Directory with *_curriculum_dynamics.json")
    ap.add_argument("--out", default="reports/comparisons/curriculum_summary.csv", help="Destination CSV path")
    args = ap.parse_args()

    insights_dir = Path(args.insights_dir)
    dynamics_dir = Path(args.dynamics_dir)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    insight_index = load_insight_comparison(insights_dir)

    rows = []
    for dyn_path in sorted(dynamics_dir.glob("*_curriculum_dynamics.json")):
        course_id = dyn_path.stem.replace("_curriculum_dynamics", "")
        dyn = json.loads(dyn_path.read_text(encoding="utf-8"))
        src = insight_index.get(course_id, {})

        # detect source type by heuristic
        source_type = "youtube" if any(k in course_id.lower() for k in ("essence", "crashcourse")) else "mit"

        # state label distribution
        steps = dyn.get("steps", [])
        labels = [s.get("state_label") for s in steps if isinstance(s.get("state_label"), str)]
        total = len(labels) or 1
        def frac(name: str) -> float:
            return round(sum(1 for l in labels if l == name) / total, 3)

        rows.append({
            "course_id": course_id,
            "source_type": source_type,
            "avg_q": src.get("avg_q"),
            "avg_TED": src.get("avg_TED"),
            "avg_spread": src.get("avg_spread"),
            "avg_continuity": src.get("avg_continuity"),
            "avg_ted_trusted": src.get("avg_ted_trusted"),
            "q_slope": dyn.get("dynamics", {}).get("q_trend_slope"),
            "TED_slope": dyn.get("dynamics", {}).get("ted_trend_slope"),
            "q_mc_std": dyn.get("uncertainty", {}).get("avg_q_mc_std"),
            "ted_mc_std": dyn.get("uncertainty", {}).get("avg_ted_mc_std"),
            "phases": len(dyn.get("phases", [])),
            "pct_stuck": frac("stuck"),
            "pct_scattered": frac("scattered"),
            "pct_pivot": frac("pivot"),
            "pct_exploring": frac("exploring"),
            "pct_mixed": frac("mixed"),
        })

    fields = [
        "course_id",
        "source_type",
        "avg_q",
        "avg_TED",
        "avg_spread",
        "avg_continuity",
        "avg_ted_trusted",
        "q_slope",
        "TED_slope",
        "q_mc_std",
        "ted_mc_std",
        "phases",
        "pct_stuck",
        "pct_scattered",
        "pct_pivot",
        "pct_exploring",
        "pct_mixed",
    ]
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print(f"Wrote {len(rows)} rows to {out_path}")


if __name__ == "__main__":
    main()

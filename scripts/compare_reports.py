#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean


def load_insights(dir_path: Path) -> dict:
    cmp = json.loads((dir_path / "comparison.json").read_text(encoding="utf-8"))
    return {row["course_id"]: row for row in cmp}


def avg_ted_trusted_from_dynamics(dyn_path: Path) -> float | None:
    try:
        dyn = json.loads(dyn_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    vals = []
    for s in dyn.get("steps", []):
        v = s.get("ted_trusted")
        if isinstance(v, (int, float)):
            vals.append(float(v))
        # sometimes reporters attach in meta; capture both
        elif isinstance(s, dict) and "ted_trusted" in s:
            try:
                vals.append(float(s["ted_trusted"]))
            except Exception:
                pass
    return round(mean(vals), 3) if vals else None


def main() -> None:
    ap = argparse.ArgumentParser(description="Compare two report runs and summarize deltas")
    ap.add_argument("--prev-insights", required=True)
    ap.add_argument("--prev-dynamics", required=True)
    ap.add_argument("--new-insights", required=True)
    ap.add_argument("--new-dynamics", required=True)
    ap.add_argument("--out-json", default="reports/comparisons/compare_v2.json")
    ap.add_argument("--out-md", default="reports/comparisons/compare_v2.md")
    args = ap.parse_args()

    prev_ins = load_insights(Path(args.prev_insights))
    new_ins = load_insights(Path(args.new_insights))

    rows = []
    all_courses = sorted(set(prev_ins) | set(new_ins))
    for cid in all_courses:
        p = prev_ins.get(cid, {})
        n = new_ins.get(cid, {})
        row = {
            "course_id": cid,
            "avg_q": {"prev": p.get("avg_q"), "new": n.get("avg_q")},
            "avg_ted": {"prev": p.get("avg_ted"), "new": n.get("avg_ted")},
            "avg_spread": {"prev": p.get("avg_spread"), "new": n.get("avg_spread")},
            "avg_continuity": {"prev": p.get("avg_continuity"), "new": n.get("avg_continuity")},
        }
        # compute avg ted_trusted in new dynamics
        dyn_prev = Path(args.prev_dynamics) / f"{cid}_curriculum_dynamics.json"
        dyn_new = Path(args.new_dynamics) / f"{cid}_curriculum_dynamics.json"
        row["avg_ted_trusted"] = {
            "prev": avg_ted_trusted_from_dynamics(dyn_prev),
            "new": avg_ted_trusted_from_dynamics(dyn_new),
        }
        rows.append(row)

    outj = Path(args.out_json)
    outj.parent.mkdir(parents=True, exist_ok=True)
    outj.write_text(json.dumps(rows, indent=2), encoding="utf-8")

    outmd = Path(args.out_md)
    with outmd.open("w", encoding="utf-8") as f:
        f.write("# Report Comparison (Prev vs New)\n\n")
        f.write("| course_id | avg_q (p→n) | avg_ted (p→n) | avg_spread (p→n) | avg_continuity (p→n) | avg_ted_trusted (p→n) |\n")
        f.write("|---|---|---|---|---|---|\n")
        for r in rows:
            def fmt(k):
                d = r[k]
                return f"{d['prev']} → {d['new']}"
            f.write(
                f"| {r['course_id']} | {fmt('avg_q')} | {fmt('avg_ted')} | {fmt('avg_spread')} | {fmt('avg_continuity')} | {fmt('avg_ted_trusted')} |\n"
            )
    print(f"Wrote {outj} and {outmd}")


if __name__ == "__main__":
    main()


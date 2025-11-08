#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


def _choose_title_from_top_nodes(top_nodes: List[Dict[str, Any]]) -> str | None:
    if not top_nodes:
        return None
    def score(label: str) -> tuple[int, int]:
        l = label or ""
        ll = l.lower()
        s = 0
        if ":" in l or "|" in l:
            s += 3
        if any(k in ll for k in ("chapter", "session", "lecture", "part")):
            s += 2
        if " " in l:
            s += 1
        # slight penalty for very long labels
        penalty = -1 if len(l) > 90 else 0
        return (s + penalty, len(l))
    # pick highest score; break ties with shorter label
    labeled = [(tn, tn.get("label") or "") for tn in top_nodes if tn.get("label")]
    if not labeled:
        return None
    best = max(labeled, key=lambda p: score(str(p[1])))
    return str(best[1])


def top_pivots_for_course(dyn: Dict[str, Any], top_n: int = 3) -> List[Dict[str, Any]]:
    steps = dyn.get("steps", [])
    # filter steps with ted_delta numeric
    candidates = [s for s in steps if isinstance(s.get("ted_delta"), (int, float))]
    candidates.sort(key=lambda s: s.get("ted_delta", 0.0), reverse=True)
    result = []
    for s in candidates[:top_n]:
        # attempt to pick a human-friendly title from top_nodes
        title = _choose_title_from_top_nodes(s.get("top_nodes") or [])
        result.append({
            "step": s.get("step"),
            "ted_delta": s.get("ted_delta"),
            "q": s.get("q"),
            "ted": s.get("ted"),
            "title": title or "(no title)",
        })
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description="Extract top TED pivots per course from dynamics reports")
    ap.add_argument("--dynamics-dir", default="reports/yt_dynamics")
    ap.add_argument("--out-json", default="reports/comparisons/top_pivots.json")
    ap.add_argument("--out-md", default="reports/comparisons/top_pivots.md")
    ap.add_argument("--top-n", type=int, default=3)
    args = ap.parse_args()

    dyn_dir = Path(args.dynamics_dir)
    out_json = Path(args.out_json)
    out_md = Path(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)

    summary: Dict[str, List[Dict[str, Any]]] = {}
    for dyn_path in sorted(dyn_dir.glob("*_curriculum_dynamics.json")):
        dyn = json.loads(dyn_path.read_text(encoding="utf-8"))
        course_id = dyn.get("run_meta", {}).get("dataset") or dyn_path.stem
        course_id = Path(str(course_id)).stem.replace("_curriculum_dynamics", "")
        summary[course_id] = top_pivots_for_course(dyn, top_n=args.top_n)

    out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    with out_md.open("w", encoding="utf-8") as f:
        f.write("# Top TED Pivots per Course\n\n")
        for course, pivots in summary.items():
            f.write(f"## {course}\n\n")
            if not pivots:
                f.write("(no pivots found)\n\n")
                continue
            for p in pivots:
                title = p.get("title") or "(no title)"
                try:
                    dted = float(p.get("ted_delta"))
                except (TypeError, ValueError):
                    dted = 0.0
                f.write(f"- step {p.get('step')}: dTED={dted:.3f} | {title}\n")
            f.write("\n")

    print(f"Wrote {len(summary)} courses to {out_json} and {out_md}")


if __name__ == "__main__":
    main()

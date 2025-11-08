#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Any, List


def _read_json_files(dir_path: Path) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if not dir_path.exists():
        return out
    for fp in dir_path.glob("*.json"):
        try:
            out[fp.stem] = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            # skip non-JSON or large files we don't need here
            continue
    return out


def summarize_courses(insights: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = []
    for name, rep in insights.items():
        if name == "comparison":
            continue
        # Some entries (e.g., index) may be lists; skip those
        if isinstance(rep, list):
            continue
        agg = (rep or {}).get("aggregates") or {}
        rows.append({
            "course": name,
            "avg_q": agg.get("avg_q"),
            "avg_ted": agg.get("avg_ted"),
            "avg_spread": agg.get("avg_spread"),
            "steps": agg.get("steps") or (rep.get("run_meta") or {}).get("steps"),
        })
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description="Combine curriculum and conversation reports into a comprehensive summary")
    ap.add_argument("--curriculum-insights", required=True)
    ap.add_argument("--curriculum-dynamics", required=True)
    ap.add_argument("--conversation-insights", required=True)
    ap.add_argument("--conversation-dynamics", required=True)
    ap.add_argument("--out-dir", default="reports/comprehensive")
    args = ap.parse_args()

    cur_ins_dir = Path(args.curriculum_insights)
    cur_dyn_dir = Path(args.curriculum_dynamics)
    con_ins_dir = Path(args.conversation_insights)
    con_dyn_dir = Path(args.conversation_dynamics)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    cur_ins = _read_json_files(cur_ins_dir)
    con_ins = _read_json_files(con_ins_dir)

    # Light summary tables
    cur_summary = summarize_courses(cur_ins)
    con_summary = summarize_courses(con_ins)

    combined = {
        "curriculum": {
            "summary": cur_summary,
            "comparison": cur_ins.get("comparison"),
        },
        "conversation": {
            "summary": con_summary,
            # conversation health index.json lives in conversation_insight_fs
            "index": con_ins.get("index"),
        },
        "meta": {
            "curriculum_insights_dir": str(cur_ins_dir),
            "curriculum_dynamics_dir": str(cur_dyn_dir),
            "conversation_insights_dir": str(con_ins_dir),
            "conversation_dynamics_dir": str(con_dyn_dir),
        }
    }

    # Write JSON
    (out_dir / "combined.json").write_text(json.dumps(combined, indent=2), encoding="utf-8")

    # Write a concise Markdown overview
    md_lines = [
        "# Comprehensive Report (Curriculum + Conversation)",
        "",
        "## Curriculum Summary",
    ]
    for r in cur_summary:
        md_lines.append(f"- {r['course']}: avg_q={r['avg_q']}, avg_ted={r['avg_ted']}, steps={r['steps']}")
    md_lines += ["", "## Conversation Summary"]
    for r in con_summary:
        md_lines.append(f"- {r['course']}: avg_q={r.get('avg_q')}, avg_ted={r.get('avg_ted')}, steps={r.get('steps')}")

    (out_dir / "combined.md").write_text("\n".join(md_lines), encoding="utf-8")


if __name__ == "__main__":
    main()

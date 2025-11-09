#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Any, List
import re


def _slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[\s+/]+", "_", s)
    s = re.sub(r"[^a-z0-9_]+", "", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s


def _canonical_conversation_key(insight_name: str) -> str:
    """Map a conversation insight filename stem to the sidecar key.

    Example:
      insight_name = "Oprah with ... _parsed.metrics" ->
      sidecar key  = "conversation_oprah_with_prince_harry_and_meghan_markle_interview_transcript_by_kate_shaw_medium"
    """
    base = insight_name
    base = base.replace("_parsed.metrics", "")
    base = base.replace(".metrics", "")
    slug = _slugify(base)
    return f"conversation_{slug}"


def _read_json_files(dir_path: Path) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if not dir_path.exists():
        return out
    for fp in dir_path.glob("*.json"):
        try:
            out[fp.stem] = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            continue
    return out


def summarize_courses(insights: Dict[str, Any], units_map: Dict[str, Any] | None = None, topics_map: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    rows = []
    for name, rep in insights.items():
        if name == "comparison":
            continue
        if isinstance(rep, list):
            continue
        if isinstance(rep, dict) and rep.get("aggregates"):
            agg = rep.get("aggregates") or {}
            row = {
                "course": name,
                "avg_q": agg.get("avg_q"),
                "avg_ted": agg.get("avg_ted"),
                "avg_spread": agg.get("avg_spread"),
                "steps": agg.get("steps") or (rep.get("run_meta") or {}).get("steps"),
            }
        elif isinstance(rep, dict) and rep.get("summary"):
            summ = rep.get("summary") or {}
            row = {
                "course": name,
                "avg_q": summ.get("avg_q"),
                "avg_ted": summ.get("avg_TED") if summ.get("avg_TED") is not None else summ.get("avg_ted"),
                "avg_spread": summ.get("avg_spread"),
                "steps": summ.get("total_turns") or (len(rep.get("signals") or []) if rep.get("signals") is not None else None),
            }
        else:
            row = {"course": name, "avg_q": None, "avg_ted": None, "avg_spread": None, "steps": None}
        # Attach sidecars when names match exactly (curriculum) or via canonical mapping (conversation)
        if units_map:
            if name in units_map and isinstance(units_map[name], dict):
                row["avg_unit_count"] = units_map[name].get("avg_unit_count")
            else:
                conv_key = _canonical_conversation_key(name)
                if conv_key in units_map and isinstance(units_map[conv_key], dict):
                    row["avg_unit_count"] = units_map[conv_key].get("avg_unit_count")
        if topics_map:
            if name in topics_map and isinstance(topics_map[name], dict):
                row["avg_ted_js"] = topics_map[name].get("avg_ted_js")
            else:
                conv_key = _canonical_conversation_key(name)
                if conv_key in topics_map and isinstance(topics_map[conv_key], dict):
                    row["avg_ted_js"] = topics_map[conv_key].get("avg_ted_js")
        rows.append(row)
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

    units_dir = Path("reports/comprehensive/graph_units")
    topics_dir = Path("reports/comprehensive/topics_js")
    units = _read_json_files(units_dir) if units_dir.exists() else {}
    topics = _read_json_files(topics_dir) if topics_dir.exists() else {}

    cur_summary = summarize_courses(cur_ins, units, topics)
    con_summary = summarize_courses(con_ins, units, topics)

    combined = {
        "curriculum": {
            "summary": cur_summary,
            "comparison": cur_ins.get("comparison"),
            "units": {k: v.get("avg_unit_count") for k, v in units.items() if isinstance(v, dict)} if units else None,
            "topics": {k: v.get("avg_ted_js") for k, v in topics.items() if isinstance(v, dict)} if topics else None,
        },
        "conversation": {
            "summary": con_summary,
            "index": con_ins.get("index"),
            "units": {k: v.get("avg_unit_count") for k, v in units.items() if isinstance(v, dict) and k.startswith("conversation_")} if units else None,
            "topics": {k: v.get("avg_ted_js") for k, v in topics.items() if isinstance(v, dict) and k.startswith("conversation_")} if topics else None,
        },
        "meta": {
            "curriculum_insights_dir": str(cur_ins_dir),
            "curriculum_dynamics_dir": str(cur_dyn_dir),
            "conversation_insights_dir": str(con_ins_dir),
            "conversation_dynamics_dir": str(con_dyn_dir),
        }
    }

    (out_dir / "combined.json").write_text(json.dumps(combined, indent=2), encoding="utf-8")

    md_lines = [
        "# Comprehensive Report (Curriculum + Conversation)",
        "",
        "## Curriculum Summary",
    ]
    for r in cur_summary:
        parts = [f"avg_q={r.get('avg_q')}", f"avg_ted={r.get('avg_ted')}", f"steps={r.get('steps')}"]
        if r.get("avg_unit_count") is not None:
            parts.append(f"units≈{round(r['avg_unit_count'],2)}")
        if r.get("avg_ted_js") is not None:
            parts.append(f"ted_js≈{round(r['avg_ted_js'],3)}")
        md_lines.append(f"- {r['course']}: " + ", ".join(parts))
    md_lines += ["", "## Conversation Summary"]
    for r in con_summary:
        parts = [f"avg_q={r.get('avg_q')}", f"avg_ted={r.get('avg_ted')}", f"steps={r.get('steps')}"]
        if r.get("avg_unit_count") is not None:
            parts.append(f"threads≈{round(r['avg_unit_count'],2)}")
        if r.get("avg_ted_js") is not None:
            parts.append(f"ted_js≈{round(r['avg_ted_js'],3)}")
        md_lines.append(f"- {r['course']}: " + ", ".join(parts))

    (out_dir / "combined.md").write_text("\n".join(md_lines), encoding="utf-8")


if __name__ == "__main__":
    main()

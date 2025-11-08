#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from pathlib import Path


def read_csv(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def write_markdown(rows, out_md: Path):
    out_md.parent.mkdir(parents=True, exist_ok=True)
    headers = [
        "course_id",
        "source_type",
        "avg_q",
        "avg_TED",
        "avg_spread",
        "avg_continuity",
        "q_slope",
        "TED_slope",
        "q_mc_std",
        "ted_mc_std",
        "phases",
    ]
    with out_md.open("w", encoding="utf-8") as f:
        f.write("# Curriculum Summary\n\n")
        f.write("| " + " | ".join(headers) + " |\n")
        f.write("|" + "|".join(["---"] * len(headers)) + "|\n")
        for r in rows:
            f.write("| " + " | ".join(str(r.get(h, "")) for h in headers) + " |\n")


def write_html(rows, out_html: Path):
    out_html.parent.mkdir(parents=True, exist_ok=True)
    headers = [
        "course_id",
        "source_type",
        "avg_q",
        "avg_TED",
        "avg_spread",
        "avg_continuity",
        "q_slope",
        "TED_slope",
        "q_mc_std",
        "ted_mc_std",
        "phases",
    ]
    with out_html.open("w", encoding="utf-8") as f:
        f.write("<html><head><meta charset='utf-8'><title>Curriculum Summary</title>\n")
        f.write("<style>body{font-family:sans-serif} table{border-collapse:collapse} td,th{border:1px solid #ddd;padding:6px} th{background:#f5f5f5}</style>")
        f.write("</head><body>\n<h1>Curriculum Summary</h1>\n<table>\n<tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr>\n")
        for r in rows:
            f.write("<tr>" + "".join(f"<td>{r.get(h,'')}</td>" for h in headers) + "</tr>\n")
        f.write("</table>\n</body></html>")


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate Markdown/HTML dashboards from curriculum CSV")
    ap.add_argument("--csv", default="reports/comparisons/curriculum_summary.csv")
    ap.add_argument("--out-md", default="reports/comparisons/curriculum_summary.md")
    ap.add_argument("--out-html", default="reports/comparisons/curriculum_summary.html")
    args = ap.parse_args()

    rows = read_csv(Path(args.csv))
    write_markdown(rows, Path(args.out_md))
    write_html(rows, Path(args.out_html))
    print(f"Wrote {len(rows)} rows to {args.out_md} and {args.out_html}")


if __name__ == "__main__":
    main()


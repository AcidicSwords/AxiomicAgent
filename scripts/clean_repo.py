#!/usr/bin/env python
from __future__ import annotations

"""
List (and optionally remove) likely build artifacts and bulky intermediates.

Defaults to dry-run; pass --delete to actually remove.

Candidates:
- Root *.zip bundles (e.g., AxiomicAgent.zip)
- reports/* (kept by default; can remove with --reports)
- RawOCW/RawYT caches (kept by default)
"""

import argparse
from pathlib import Path


def collect_candidates(include_reports: bool = False) -> list[Path]:
    root = Path.cwd()
    candidates: list[Path] = []
    # root zips
    for p in root.glob("*.zip"):
        candidates.append(p)
    if include_reports:
        rep = root / "reports"
        if rep.exists():
            for p in rep.rglob("*.json"):
                candidates.append(p)
            for p in rep.rglob("*.md"):
                candidates.append(p)
            for p in rep.rglob("*.html"):
                candidates.append(p)
            for p in rep.rglob("*.csv"):
                candidates.append(p)
    return candidates


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--delete", action="store_true", help="Delete listed files")
    ap.add_argument("--reports", action="store_true", help="Also include reports/* in candidates")
    args = ap.parse_args()

    cands = collect_candidates(include_reports=args.reports)
    if not cands:
        print("No candidates found.")
        return

    print("Candidates:")
    for p in cands:
        print(" -", p)

    if args.delete:
        for p in cands:
            try:
                p.unlink()
            except Exception as e:
                print(f"Failed to remove {p}: {e}")
        print(f"Removed {len(cands)} files.")
    else:
        print("(dry-run; pass --delete to remove)")


if __name__ == "__main__":
    main()


#!/usr/bin/env python
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import adapters  # noqa: F401  ensures adapter registration
import reporters  # noqa: F401  ensures reporter registration
from core.engine import Engine


def main() -> None:
    parser = argparse.ArgumentParser(description="Run insight pipeline on a dataset zip.")
    parser.add_argument("--adapter", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--reporter", default="insight")
    parser.add_argument("--reporter-domain", default="generic")
    parser.add_argument("--output", default="reports/insight_summary.json")
    args = parser.parse_args()

    engine = Engine(
        adapter=args.adapter,
        dataset_path=args.dataset,
        reporter=args.reporter,
        reporter_kwargs={"domain": args.reporter_domain, "path": args.output},
    )
    engine.run()


if __name__ == "__main__":
    main()

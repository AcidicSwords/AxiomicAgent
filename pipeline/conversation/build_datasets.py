#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from scripts.build_conversation_datasets import main as _impl


def main() -> None:
    _impl()


if __name__ == "__main__":
    main()

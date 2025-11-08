from __future__ import annotations

from adapters.base import RawStream
from adapters.base import load_zip_stream, load_fs_stream
from pathlib import Path


def extract(path: str) -> RawStream:
    """Extract RawStream from a curriculum dataset path (zip or directory)."""
    p = Path(path)
    if p.is_dir():
        return load_fs_stream(p)
    return load_zip_stream(p)

from __future__ import annotations

from adapters.base import RawStream
from adapters.base import load_zip_stream


def extract(path: str) -> RawStream:
    return load_zip_stream(path)

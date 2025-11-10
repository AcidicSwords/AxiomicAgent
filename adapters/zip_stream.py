from __future__ import annotations

from core.registry import REG
from adapters.curriculum.stream import CurriculumStream

# Legacy alias so existing configs using adapter="zip_stream" continue to work.
REG.adapters["zip_stream"] = CurriculumStream

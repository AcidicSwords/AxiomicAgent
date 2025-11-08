from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

from builders.curriculum import CurriculumBuilderParams, build_from_items_json


@dataclass
class CurriculumBuilderConfig(CurriculumBuilderParams):
    """
    Deprecated alias preserved for compatibility.
    """


def build_dataset_from_json(
    input_paths: Sequence[Path],
    output_zip: Path,
    config: Optional[CurriculumBuilderConfig] = None,
) -> None:
    if not input_paths:
        raise ValueError("No curriculum item JSON provided.")
    if len(input_paths) > 1:
        raise ValueError("Only a single curriculum JSON input is supported.")

    params = config or CurriculumBuilderConfig()
    build_from_items_json(input_paths[0], output_zip, params)

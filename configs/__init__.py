from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

from .datasets import (
    ConversationDatasetConfig,
    CurriculumDatasetConfig,
    DatasetConfig,
    load_dataset_config,
)

__all__ = [
    "ConversationDatasetConfig",
    "CurriculumDatasetConfig",
    "DatasetConfig",
    "load_dataset_config",
]


def resolve_config(target: Union[str, Path], *, search_dir: Optional[Path] = None) -> DatasetConfig:
    """
    Convenience helper used by scripts to turn either a name (e.g. \"curriculum\")
    or a path into a concrete DatasetConfig instance.
    """
    return load_dataset_config(target, search_dir=search_dir)


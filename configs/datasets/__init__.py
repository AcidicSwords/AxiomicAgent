from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Union


CONFIG_ROOT = Path(__file__).resolve().parents[2]


class DatasetConfigError(ValueError):
    """Raised when a dataset configuration JSON cannot be parsed."""


@dataclass(slots=True)
class DatasetConfig:
    domain: str


@dataclass(slots=True)
class ConversationBuilderConfig:
    source: Path
    output: Path
    chunk_size: int = 20
    stride: int = 10
    max_steps: Optional[int] = None
    token_window: int = 2
    top_n_terms: int = 500
    max_ngram: int = 5
    top_global_edges: int = 500
    max_edges_per_step: int = 150
    roles: List[str] = field(default_factory=lambda: ["user", "assistant"])
    min_chars: int = 12
    drop_regex: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any], *, base_dir: Path) -> "ConversationBuilderConfig":
        if "source" not in data or "output" not in data:
            raise DatasetConfigError("conversation builder config requires 'source' and 'output'")
        return cls(
            source=_resolve_path(data["source"], base_dir),
            output=_resolve_path(data["output"], base_dir),
            chunk_size=int(data.get("chunk_size", cls.chunk_size)),
            stride=int(data.get("stride", cls.stride)),
            max_steps=_optional_int(data.get("max_steps")),
            token_window=int(data.get("token_window", cls.token_window)),
            top_n_terms=int(data.get("top_n_terms", cls.top_n_terms)),
            max_ngram=int(data.get("max_ngram", cls.max_ngram)),
            top_global_edges=int(data.get("top_global_edges", cls.top_global_edges)),
            max_edges_per_step=int(data.get("max_edges_per_step", cls.max_edges_per_step)),
            roles=list(_clean_iterable(data.get("roles"), default=["user", "assistant"])),
            min_chars=int(data.get("min_chars", cls.min_chars)),
            drop_regex=_optional_str(data.get("drop_regex")),
        )


@dataclass(slots=True)
class ConversationPreprocessorConfig:
    stop_terms: List[str] = field(default_factory=list)
    degree_cap: int = 120
    min_length: int = 3

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationPreprocessorConfig":
        return cls(
            stop_terms=list(_clean_iterable(data.get("stop_terms"), default=[])),
            degree_cap=int(data.get("degree_cap", cls.degree_cap)),
            min_length=int(data.get("min_length", cls.min_length)),
        )


@dataclass(slots=True)
class ConversationDatasetConfig(DatasetConfig):
    builder: ConversationBuilderConfig
    preprocessor: ConversationPreprocessorConfig


@dataclass(slots=True)
class CurriculumBuilderConfig:
    source: Path
    output: Path
    max_steps: Optional[int] = None
    max_children: Optional[int] = None
    include_sibling_links: bool = True
    keep_running_ancestor_edges: bool = True

    @classmethod
    def from_dict(cls, data: Dict[str, Any], *, base_dir: Path) -> "CurriculumBuilderConfig":
        if "source" not in data or "output" not in data:
            raise DatasetConfigError("curriculum builder config requires 'source' and 'output'")
        return cls(
            source=_resolve_path(data["source"], base_dir),
            output=_resolve_path(data["output"], base_dir),
            max_steps=_optional_int(data.get("max_steps")),
            max_children=_optional_int(data.get("max_children")),
            include_sibling_links=bool(data.get("include_sibling_links", cls.include_sibling_links)),
            keep_running_ancestor_edges=bool(data.get("keep_running_ancestor_edges", cls.keep_running_ancestor_edges)),
        )


@dataclass(slots=True)
class CurriculumTypeRule:
    type: str
    weight: float
    match: List[str] = field(default_factory=list)
    pattern: str | None = None
    tag: str | None = None


@dataclass(slots=True)
class CurriculumPreprocessorConfig:
    stop_nodes: List[str] = field(default_factory=list)
    regex_patterns: List[str] = field(default_factory=list)
    type_rules: List[CurriculumTypeRule] = field(default_factory=list)
    keep_threshold: float = 0.10
    topk_per_node: int = 50

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CurriculumPreprocessorConfig":
        rules = []
        for entry in data.get("type_rules", []):
            if not isinstance(entry, dict):
                continue
            rule = CurriculumTypeRule(
                type=str(entry.get("type") or "unknown"),
                weight=float(entry.get("weight", 1.0)),
                match=[str(m).lower() for m in _clean_iterable(entry.get("match"), default=[])],
                pattern=str(entry["pattern"]) if entry.get("pattern") else None,
                tag=str(entry.get("tag")) if entry.get("tag") else None,
            )
            rules.append(rule)
        return cls(
            stop_nodes=list(_clean_iterable(data.get("stop_nodes"), default=[])),
            regex_patterns=list(_clean_iterable(data.get("regex_patterns"), default=[])),
            type_rules=rules,
            keep_threshold=float(data.get("keep_threshold", cls.keep_threshold)),
            topk_per_node=int(data.get("topk_per_node", cls.topk_per_node)),
        )


@dataclass(slots=True)
class CurriculumDatasetConfig(DatasetConfig):
    builder: CurriculumBuilderConfig
    preprocessor: CurriculumPreprocessorConfig


def load_dataset_config(target: Union[str, Path], *, search_dir: Optional[Path] = None) -> DatasetConfig:
    """
    Load a dataset configuration JSON file. ``target`` can be either a path or a stem
    (\"conversation\" -> configs/datasets/conversation.json).
    """
    cfg_path = _resolve_config_path(target, search_dir=search_dir)
    payload = json.loads(cfg_path.read_text(encoding="utf-8"))

    domain = str(payload.get("domain") or "").strip().lower()
    if not domain:
        raise DatasetConfigError(f"dataset config {cfg_path} missing 'domain'")

    base_dir = cfg_path.parent
    if domain == "conversation":
        builder_dict = _require_dict(payload, "builder")
        preproc_dict = _require_dict(payload, "preprocessor")
        return ConversationDatasetConfig(
            domain=domain,
            builder=ConversationBuilderConfig.from_dict(builder_dict, base_dir=base_dir),
            preprocessor=ConversationPreprocessorConfig.from_dict(preproc_dict),
        )
    if domain == "curriculum":
        builder_dict = _require_dict(payload, "builder")
        preproc_dict = _require_dict(payload, "preprocessor")
        return CurriculumDatasetConfig(
            domain=domain,
            builder=CurriculumBuilderConfig.from_dict(builder_dict, base_dir=base_dir),
            preprocessor=CurriculumPreprocessorConfig.from_dict(preproc_dict),
        )
    raise DatasetConfigError(f"Unsupported dataset domain '{domain}' in {cfg_path}")


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


def _resolve_config_path(target: Union[str, Path], *, search_dir: Optional[Path]) -> Path:
    if isinstance(target, Path):
        if target.is_file():
            return target
        target = target.as_posix()
    if isinstance(target, str):
        path = Path(target)
        if path.is_file():
            return path
        if not path.suffix:
            default_dir = search_dir or Path(__file__).resolve().parent
            candidate = default_dir / f"{path}.json"
            if candidate.is_file():
                return candidate
        raise DatasetConfigError(f"could not locate dataset config '{target}'")
    raise DatasetConfigError(f"unsupported config target type: {type(target)!r}")


def _resolve_path(value: Union[str, Path], base_dir: Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path

    text = path.as_posix()
    if text.startswith("./") or text.startswith(".\\"):
        return (base_dir / path).resolve()

    candidate = (CONFIG_ROOT / path).resolve()
    if candidate.exists() or not (base_dir / path).exists():
        return candidate
    return (base_dir / path).resolve()


def _optional_int(value: Any) -> Optional[int]:
    if value in (None, "", False):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        raise DatasetConfigError(f"expected integer value, got {value!r}") from None


def _optional_str(value: Any) -> Optional[str]:
    if value in (None, "", False):
        return None
    return str(value)


def _clean_iterable(value: Any, *, default: Iterable[str]) -> Iterable[str]:
    if not value:
        return list(default)
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)]


def _require_dict(container: Dict[str, Any], key: str) -> Dict[str, Any]:
    value = container.get(key)
    if not isinstance(value, dict):
        raise DatasetConfigError(f"section '{key}' missing or not an object")
    return value

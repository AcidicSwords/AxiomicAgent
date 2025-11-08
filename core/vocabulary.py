from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, List


@dataclass(frozen=True)
class AdapterVocabulary:
    adapter_id: str
    aliases: List[str]
    intent_markers: List[str]
    node_markers: List[str]
    edge_markers: List[str]
    llm_verbs: List[str]


def _terms_path() -> Path:
    return Path(__file__).resolve().parents[1] / "configs" / "adapter_terms.json"


@lru_cache(maxsize=1)
def _load_all_vocab() -> Dict[str, AdapterVocabulary]:
    path = _terms_path()
    if not path.exists():
        return {}

    payload = json.loads(path.read_text(encoding="utf-8"))
    vocab: Dict[str, AdapterVocabulary] = {}
    for entry in payload.get("adapters", []):
        adapter_id = entry.get("id")
        if not adapter_id:
            continue
        vocab[adapter_id] = AdapterVocabulary(
            adapter_id=adapter_id,
            aliases=list(entry.get("aliases", [])),
            intent_markers=list(entry.get("intent_markers", [])),
            node_markers=list(entry.get("node_markers", [])),
            edge_markers=list(entry.get("edge_markers", [])),
            llm_verbs=list(entry.get("llm_verbs", [])),
        )
    return vocab


def get_adapter_vocab(adapter_id: str) -> AdapterVocabulary | None:
    return _load_all_vocab().get(adapter_id)


def list_adapter_vocab() -> Dict[str, AdapterVocabulary]:
    return dict(_load_all_vocab())

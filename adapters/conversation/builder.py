"""Conversation dataset builder.

Transforms raw conversation logs into the canonical dataset zip consumed by the
core engine. Lives alongside the adapter so domain-specific heuristics stay out
of the core. Typical entry points:

    python scripts/build_dataset.py --config configs/datasets/conversation.json
    python scripts/build_dataset.py conversation --source ... --out ...
"""

from __future__ import annotations

import json
import re
from collections import Counter, deque
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from adapters.base.zip_writer import write_dataset_zip
from configs.datasets import (
    ConversationBuilderConfig,
    ConversationDatasetConfig,
    ConversationPreprocessorConfig,
)

STOP_TERMS = {
    "the",
    "and",
    "or",
    "but",
    "if",
    "in",
    "on",
    "at",
    "to",
    "for",
    "with",
    "a",
    "an",
    "of",
    "is",
    "it",
    "this",
    "that",
    "be",
    "are",
    "as",
    "by",
    "from",
    "was",
    "were",
    "do",
    "does",
    "did",
    "about",
    "into",
    "out",
    "up",
    "down",
    "off",
    "over",
    "under",
    "than",
    "so",
    "such",
    "just",
    "well",
    "very",
    "have",
    "has",
    "had",
    "we",
    "you",
    "they",
    "them",
    "their",
    "our",
    "i",
    "me",
    "my",
    "your",
    "not",
    "",
    "-",
    "_",
}

CODE_TERMS = {
    "function",
    "func",
    "def",
    "class",
    "const",
    "let",
    "var",
    "return",
    "printf",
    "cout",
    "include",
    "import",
    "public",
    "private",
    "static",
    "void",
    "null",
    "true",
    "false",
    "bool",
    "int",
    "float",
    "double",
    "struct",
    "enum",
    "namespace",
    "override",
    "implements",
    "extends",
    "lambda",
    "async",
    "await",
    "yield",
    "foreach",
    "while",
    "loop",
    "endif",
    "elseif",
    "switch",
    "case",
    "break",
    "continue",
    "template",
    "typename",
    "package",
    "module",
    "new",
    "delete",
    "throw",
    "catch",
    "str",
    "self",
}

CODE_CHARS = set("{}[]();<>:+-=*/\\\"'")

RE_CODE_FENCE = re.compile(r"```.*?```", re.DOTALL)
RE_URL = re.compile(r"https?://\S+")
RE_META_BLOCK = re.compile(r"^\[[^\]]{3,120}\]$", re.MULTILINE)
RE_EMPTY_LINES = re.compile(r"\n{2,}")
RE_PROMPT_UI = re.compile(
    r"^(Thought for \d+s|Reasoning|Navigation list|Image carousel|Sports schedule)\b.*$",
    re.MULTILINE | re.IGNORECASE,
)
IGNORE_CONTENT_TYPES = {"thoughts", "reasoning_recap", "code", "tool", "system_error"}
DEFAULT_ROLES = {"user", "assistant"}


# --------------------------------------------------------------------------- #
# Text cleaning helpers
# --------------------------------------------------------------------------- #


def clean_text(text: str) -> str:
    """Remove UI / code artefacts so the tokeniser sees natural language."""
    if not text:
        return ""
    text = RE_CODE_FENCE.sub(" ", text)
    text = RE_PROMPT_UI.sub(" ", text)
    text = RE_META_BLOCK.sub(" ", text)
    text = RE_URL.sub(" ", text)
    text = RE_EMPTY_LINES.sub("\n", text)
    return text.replace("\u200b", "").strip()


def tokenize(text: str) -> List[str]:
    """Simple alphanumeric tokeniser with stop-term filtering."""
    tokens: List[str] = []
    buf: List[str] = []
    for ch in text.lower():
        if ch.isalpha() or ch.isdigit():
            buf.append(ch)
        else:
            if buf:
                tokens.append("".join(buf))
                buf = []
    if buf:
        tokens.append("".join(buf))

    cleaned: List[str] = []
    for token in tokens:
        if len(token) < 3:
            continue
        if token in STOP_TERMS or token in CODE_TERMS:
            continue
        if any(char in token for char in CODE_CHARS):
            continue
        if "_" in token or token.isdigit():
            continue
        if len(token) > 4 and all(c in "0123456789abcdef" for c in token):
            continue  # likely a hash
        cleaned.append(token)
    return cleaned


def expand_terms(tokens: List[str], max_ngram: int) -> List[Tuple[str, int]]:
    """Enumerate 1..N-gram terms with their starting position."""
    out: List[Tuple[str, int]] = []
    n = len(tokens)
    for i in range(n):
        out.append((tokens[i], i))
        for j in range(i + 2, min(i + max_ngram + 1, n + 1)):
            out.append((" ".join(tokens[i:j]), i))
    return out


# --------------------------------------------------------------------------- #
# Conversation traversal
# --------------------------------------------------------------------------- #


def _iter_openai_mapping(
    mapping: Dict[str, Any],
    roles: Set[str],
    min_chars: int,
    drop_pattern: Optional[re.Pattern],
) -> Iterable[str]:
    """Traverse OpenAI-style tree, yielding cleaned message text."""
    roots = [
        nid for nid, info in mapping.items() if (info or {}).get("parent") is None
    ]

    def sort_key(nid: str) -> float:
        info = mapping.get(nid) or {}
        msg = info.get("message") or {}
        ct = msg.get("create_time") or msg.get("update_time")
        try:
            return float(ct) if ct is not None else 0.0
        except Exception:
            return 0.0

    queue: deque[str] = deque()
    for root in sorted(roots, key=sort_key):
        children = (mapping.get(root) or {}).get("children", [])
        queue.extend(sorted(children, key=sort_key))

    seen: Set[str] = set()
    while queue:
        nid = queue.popleft()
        if nid in seen:
            continue
        seen.add(nid)

        info = mapping.get(nid) or {}
        msg = info.get("message") or {}
        role = ((msg.get("author") or {}).get("role") or "").lower()
        content = msg.get("content")

        text_val = ""
        if isinstance(content, dict):
            ctype = content.get("content_type")
            if ctype in IGNORE_CONTENT_TYPES:
                text_val = ""
            elif ctype == "text" and isinstance(content.get("parts"), list):
                text_val = "\n".join(p for p in content["parts"] if isinstance(p, str))
            else:
                text_val = content.get("text") or ""
        elif isinstance(content, list):
            text_val = "\n".join(str(item) for item in content)
        elif isinstance(content, str):
            text_val = content

        text_val = clean_text(text_val)
        if role in roles and len(text_val) >= min_chars:
            if not drop_pattern or not drop_pattern.search(text_val):
                yield text_val

        children = sorted(info.get("children", []), key=sort_key)
        for child in children:
            if child not in seen:
                queue.append(child)


def iter_conversation_messages(
    path: Path,
    roles: Set[str],
    min_chars: int,
    drop_pattern: Optional[re.Pattern],
) -> Iterable[str]:
    """Yield cleaned messages from supported conversation schemas."""
    data = json.loads(path.read_text(encoding="utf-8"))

    def emit(role: str, text: str) -> Optional[str]:
        text = clean_text(text or "")
        if role in roles and len(text) >= min_chars:
            if not drop_pattern or not drop_pattern.search(text):
                return text
        return None

    if isinstance(data, dict) and "mapping" in data:
        yield from _iter_openai_mapping(data["mapping"], roles, min_chars, drop_pattern)
        return

    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and "mapping" in item:
                yield from _iter_openai_mapping(
                    item["mapping"], roles, min_chars, drop_pattern
                )
            elif isinstance(item, dict) and "messages" in item:
                for msg in item.get("messages", []):
                    role = (msg.get("role") or msg.get("author") or "").lower()
                    role = "assistant" if role in {"assistant", "ai", "bot"} else role
                    role = "user" if role in {"human", "user"} else role
                    text = msg.get("text") or msg.get("content") or ""
                    out = emit(role, text)
                    if out:
                        yield out
            elif isinstance(item, dict):
                role = (item.get("role") or item.get("author") or "").lower()
                text = item.get("text") or item.get("content") or ""
                out = emit(role, text)
                if out:
                    yield out
        return

    raise ValueError("Unsupported conversation JSON schema")


# --------------------------------------------------------------------------- #
# Graph construction
# --------------------------------------------------------------------------- #


def build_vocabulary(
    messages: Iterable[str], top_n: int, max_ngram: int
) -> Dict[str, int]:
    """Construct vocabulary of frequent tokens/n-grams."""
    counter = Counter()
    for text in messages:
        tokens = tokenize(text)
        if not tokens:
            continue
        counter.update(tokens)
        counter.update(term for term, _ in expand_terms(tokens, max_ngram))
    most_common = counter.most_common(top_n)
    return {term: idx for idx, (term, _) in enumerate(most_common)}


def compute_global_pairs(
    messages: Iterable[str],
    vocab: Dict[str, int],
    window_size: int,
    max_ngram: int,
    top_k: int,
) -> Set[Tuple[int, int]]:
    """Select globally important term pairs for later per-step filtering."""
    counts = Counter()
    for text in messages:
        tokens = tokenize(text)
        if not tokens:
            continue
        terms_by_pos = [
            (term, pos)
            for term, pos in expand_terms(tokens, max_ngram)
            if term in vocab
        ]
        if not terms_by_pos:
            continue
        for i, (term_a, pos_a) in enumerate(terms_by_pos):
            src = vocab[term_a]
            for term_b, pos_b in terms_by_pos[i + 1 :]:
                if pos_b - pos_a > window_size:
                    break
                dst = vocab[term_b]
                if src == dst:
                    continue
                pair = (src, dst) if src < dst else (dst, src)
                counts[pair] += 1
    return {pair for pair, _ in counts.most_common(top_k)}


def build_edges(
    messages: List[str],
    vocab: Dict[str, int],
    window_size: int,
    max_ngram: int,
    max_edges_per_step: int,
    allowed_pairs: Optional[Set[Tuple[int, int]]] = None,
) -> Tuple[Dict[int, str], List[Tuple[int, int, int]]]:
    """Return node label map and per-step edges."""
    nodes = {idx: term for term, idx in vocab.items()}
    edges: List[Tuple[int, int, int]] = []

    for step_idx, text in enumerate(messages):
        tokens = tokenize(text)
        if not tokens:
            continue
        terms_by_pos = [
            (term, pos)
            for term, pos in expand_terms(tokens, max_ngram)
            if term in vocab
        ]
        if not terms_by_pos:
            continue

        pair_counts = Counter()
        for i, (term_a, pos_a) in enumerate(terms_by_pos):
            src = vocab[term_a]
            for term_b, pos_b in terms_by_pos[i + 1 :]:
                if pos_b - pos_a > window_size:
                    break
                dst = vocab[term_b]
                if src == dst:
                    continue
                pair = (src, dst) if src < dst else (dst, src)
                if allowed_pairs is not None and pair not in allowed_pairs:
                    continue
                pair_counts[pair] += 1

        for (a, b), _ in pair_counts.most_common(max_edges_per_step):
            edges.append((step_idx, a, b))
            edges.append((step_idx, b, a))

    return nodes, edges


# --------------------------------------------------------------------------- #
# Entry points
# --------------------------------------------------------------------------- #


def build_dataset(config: ConversationBuilderConfig) -> None:
    """Materialise the conversation stream zip according to `config`."""
    roles = set(config.roles or DEFAULT_ROLES)
    drop_pat = (
        re.compile(config.drop_regex, re.IGNORECASE) if config.drop_regex else None
    )

    raw_messages = list(
        iter_conversation_messages(config.source, roles, config.min_chars, drop_pat)
    )
    if not raw_messages:
        raise ValueError("No messages extracted from conversation JSON")

    chunks: List[str] = []
    for start in range(0, len(raw_messages), max(1, config.stride)):
        chunk = " ".join(raw_messages[start : start + config.chunk_size]).strip()
        if chunk:
            chunks.append(chunk)
        if config.max_steps is not None and len(chunks) >= config.max_steps:
            break

    if not chunks:
        raise ValueError("No conversation chunks produced from raw data")

    vocab = build_vocabulary(chunks, config.top_n_terms, config.max_ngram)
    allowed_pairs = compute_global_pairs(
        chunks,
        vocab,
        config.token_window,
        config.max_ngram,
        config.top_global_edges,
    )
    nodes, edges = build_edges(
        chunks,
        vocab,
        config.token_window,
        config.max_ngram,
        config.max_edges_per_step,
        allowed_pairs,
    )

    meta = {
        "type": "conversation_terms_cooccurrence",
        "source": config.source.name,
        "n": len(vocab),
        "T": len(chunks),
        "window": config.token_window,
        "stride": config.stride,
        "tau": 1,
        "vocab_top_n": config.top_n_terms,
        "max_ngram": config.max_ngram,
        "chunk_size": config.chunk_size,
        "max_edges_per_step": config.max_edges_per_step,
        "top_global_edges": config.top_global_edges,
        "roles": sorted(list(roles)),
        "min_chars": config.min_chars,
        "drop_regex": config.drop_regex or "",
        "schema": {
            "edges": ["step", "src", "dst", "val"],
            "nodes": ["id", "term"],
        },
    }
    write_dataset_zip(config.output, nodes, edges, meta, node_header="term")


def build_from_config(cfg: ConversationDatasetConfig) -> None:
    """Helper used by the dispatcher: build using the dataclass config."""
    build_dataset(cfg.builder)


def buildercli_to_config(args) -> ConversationDatasetConfig:
    """Legacy CLI bridge -> config dataclass."""
    builder_cfg = ConversationBuilderConfig(
        source=Path(args.source),
        output=Path(args.out),
        top_n_terms=args.top_n,
        token_window=args.window,
        max_ngram=args.max_ngram,
        chunk_size=args.chunk_size,
        stride=args.stride,
        max_steps=args.max_steps,
        max_edges_per_step=args.max_edges_per_step,
        top_global_edges=args.top_global_edges,
        roles=[r.strip() for r in args.roles.split(",")] if args.roles else list(DEFAULT_ROLES),
        min_chars=args.min_chars,
        drop_regex=args.drop_regex or None,
    )
    return ConversationDatasetConfig(
        domain="conversation",
        builder=builder_cfg,
        preprocessor=ConversationPreprocessorConfig(),
    )


__all__ = [
    "build_dataset",
    "build_from_config",
    "buildercli_to_config",
]

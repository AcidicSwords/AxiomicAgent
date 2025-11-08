"""
Transcript utilities for YouTube:

- Parse WebVTT (.vtt) or youtube_transcript_api JSON into a canonical
  transcript structure: {"video_id": str, "segments": [{start,end,text}]}.
- Produce coarse segments (~30s) for use as segment nodes in the builder.
- Extract content-oriented keywords (phrases first, then anchor-weighted singles)
  for concept nodes and cross-step continuity/glue.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List


def from_youtube_transcript_api(video_id: str, raw: List[dict]) -> dict:
    """
    Normalize youtube_transcript_api output into a canonical transcript dict.

    Input raw is a list of {"text": str, "start": float, "duration": float}.
    Output is {"video_id": str, "segments": [{start, end, text}, ...]}.
    """
    segments: List[dict] = []
    for seg in raw or []:
        try:
            start = float(seg.get("start", 0.0))
            end = start + float(seg.get("duration", 0.0))
            text = str(seg.get("text", "")).strip()
        except (TypeError, ValueError):
            continue
        if text:
            segments.append({"start": start, "end": end, "text": text})
    return {"video_id": video_id, "segments": segments}


_VTT_TIME_RE = re.compile(
    r"^(?P<start>\d{2}:\d{2}:\d{2}\.\d{3})\s+-->\s+(?P<end>\d{2}:\d{2}:\d{2}\.\d{3})"
)


def _parse_timestamp(ts: str) -> float:
    hh, mm, rest = ts.split(":", 2)
    ss, ms = rest.split(".", 1)
    return int(hh) * 3600 + int(mm) * 60 + int(ss) + int(ms) / 1000.0


def parse_vtt_to_segments(video_id: str, vtt_path: str | Path) -> dict:
    """
    Parse a WebVTT subtitle file into canonical segments.
    """
    path = Path(vtt_path)
    if not path.exists():
        return {"video_id": video_id, "segments": []}
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    segments: List[dict] = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i].strip()
        i += 1
        if not line or line.upper() == "WEBVTT":
            continue
        m = _VTT_TIME_RE.match(line)
        if not m:
            continue
        start = _parse_timestamp(m.group("start"))
        end = _parse_timestamp(m.group("end"))
        text_lines: List[str] = []
        while i < n and lines[i].strip() and not _VTT_TIME_RE.match(lines[i]):
            text_lines.append(lines[i].strip())
            i += 1
        text = " ".join(text_lines).strip()
        if text:
            segments.append({"start": start, "end": end, "text": text})
    return {"video_id": video_id, "segments": segments}


def coarse_segments(transcript: dict, segment_duration: float = 30.0) -> List[dict]:
    """
    Group fine subtitle segments into coarser ~segment_duration windows.
    Returns a list of segments with {start, end, text}.
    """
    fine = list(transcript.get("segments") or [])
    if not fine:
        return []
    grouped: List[dict] = []
    current_start = float(fine[0].get("start", 0.0))
    current_text: List[str] = []
    last_end = current_start
    for seg in fine:
        s = float(seg.get("start", 0.0))
        e = float(seg.get("end", s))
        t = str(seg.get("text", "")).strip()
        if s - current_start > segment_duration and current_text:
            grouped.append({"start": current_start, "end": last_end, "text": " ".join(current_text)})
            current_start = s
            current_text = []
        if t:
            current_text.append(t)
        last_end = max(last_end, e)
    if current_text:
        grouped.append({"start": current_start, "end": last_end, "text": " ".join(current_text)})
    return grouped


_STOPWORDS = {
    "the",
    "and",
    "for",
    "that",
    "with",
    "this",
    "from",
    "have",
    "your",
    "what",
    "when",
    "where",
    "into",
    "about",
    "over",
    "under",
    "also",
    "they",
    "them",
    "you",
    "are",
    "was",
    "were",
    "it's",
    "its",
    "we",
    "our",
    "one",
    "two",
    "three",
    "these",
    "those",
}


_EXTRA_STOP = {
    # common non-content words that were leaking into top nodes
    "actually",
    "again",
    "also",
    "always",
    "another",
    "around",
    "because",
    "between",
    "doing",
    "every",
    "exactly",
    "getting",
    "going",
    "just",
    "kind",
    "little",
    "maybe",
    "might",
    "often",
    "okay",
    "pretty",
    "really",
    "right",
    "same",
    "something",
    "still",
    "thing",
    "think",
    "through",
    "together",
    "trying",
    "using",
    "way",
    "well",
    "without",
}

_CONTENT_ANCHORS = {
    # STEM anchors
    "derivative",
    "derivatives",
    "integral",
    "integrals",
    "limit",
    "limits",
    "series",
    "taylor",
    "matrix",
    "matrices",
    "vector",
    "vectors",
    "eigen",
    "determinant",
    "gradient",
    "differential",
    "equation",
    "equations",
    "theorem",
    "rule",
    "function",
    "functions",
    # CS anchors
    "algorithm",
    "algorithms",
    "memory",
    "network",
    "operating",
    "systems",
    "compiler",
    "data",
    # History anchors
    "empire",
    "revolution",
    "civilization",
}


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z][a-zA-Z\-']{2,}", text.lower())


def _phrases(tokens: List[str]) -> List[str]:
    # Build bigrams/trigrams; prefer if they include an anchor
    phrases: List[str] = []
    for n in (3, 2):
        for i in range(len(tokens) - n + 1):
            window = tokens[i : i + n]
            # skip if any token is a stopword-like
            if any(t in _STOPWORDS or t in _EXTRA_STOP for t in window):
                continue
            phrase = " ".join(window)
            if any(a in window for a in _CONTENT_ANCHORS):
                phrases.append(phrase)
    return phrases


def extract_keywords(text: str, max_keywords: int = 5) -> List[str]:
    """
    Content-oriented extraction:
    - tokenize and remove stopwords
    - prefer multi-word phrases containing domain anchors
    - fallback to informative single tokens (len>=5) sorted by frequency
    """
    tokens_all = _tokenize(text)
    tokens = [
        t
        for t in tokens_all
        if t not in _STOPWORDS and t not in _EXTRA_STOP and len(t) >= 5
    ]

    # Phrase candidates containing anchors
    phrases = _phrases(tokens_all)
    phrase_counts = Counter(phrases)
    top_phrases = [p for p, _ in phrase_counts.most_common(max_keywords * 2)]

    # Single-token fallback, prioritize anchors and frequency
    counts = Counter(tokens)
    singles = [w for w, _ in counts.most_common(max_keywords * 2)]
    singles = sorted(
        singles,
        key=lambda w: (0 if w in _CONTENT_ANCHORS else 1, -counts[w], w),
    )

    result: List[str] = []
    for p in top_phrases:
        if p not in result:
            result.append(p)
        if len(result) >= max_keywords:
            break
    if len(result) < max_keywords:
        for w in singles:
            if w not in result:
                result.append(w)
            if len(result) >= max_keywords:
                break
    return result[: max_keywords]

#!/usr/bin/env python
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Optional

META_PATTERNS = [
    r"^\s*edited by\\b.*$",
    r"^\s*transcript\\b.*$",
    r"^\s*subscribe\\b.*$",
    r"^\s*sign in\\b.*$",
    r"^\s*copyright\\b.*$",
    r"^\s*all rights reserved\\b.*$",
    r"^\s*(get unlimited access|become a member)\\b.*$",
    r"^\s*medium\\b.*$",
]
META_RE = [re.compile(p, re.IGNORECASE) for p in META_PATTERNS]
QUESTION_KEYWORDS = [
    "why", "how", "what", "when", "where", "who", "which",
    "did", "does", "do", "can", "could", "would", "should",
]
ROLE_MAP = {
    "justice": "Justice",
    "chief justice": "Justice",
    "justice sotomayor": "Justice",
    "justice gorsuch": "Justice",
    "solicitor general": "GovtCounsel",
    "counsel": "Advocate",
    "mr.": "Advocate",
    "mr": "Advocate",
    "ms.": "Advocate",
    "ms": "Advocate",
    "narration": "Narration",
}
STOPWORDS = {"the", "and", "or", "but", "if", "so", "because", "that", "this",
             "these", "those", "you", "your", "we", "they", "i", "a", "an"}

def sentence_split(text: str) -> List[str]:
    text = text.strip()
    if not text:
        return []
    text = re.sub(r"\s+", " ", text)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\[\(\"'])", text)
    out: List[str] = []
    for p in parts:
        p = p.strip()
        if len(p) >= 2:
            out.append(p)
    return out if out else [text]

def is_meta(line: str) -> bool:
    return any(rx.match(line) for rx in META_RE)

def is_question(text: str) -> bool:
    txt = text.strip()
    if not txt:
        return False
    if txt.endswith("?"):
        return True
    lower = txt.lower()
    return any(lower.startswith(keyword + " ") or lower.startswith(keyword + "?") for keyword in QUESTION_KEYWORDS)

def normalize_role(speaker: str) -> str:
    lower = (speaker or "").lower()
    for key, role in ROLE_MAP.items():
        if key in lower:
            return role
    return "Other"

def tokenize(text: str) -> List[str]:
    tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return tokens[:20]

def load_profile_map(path: Optional[Path]) -> List[dict]:
    if not path or not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))

def match_profile(name: str, profiles: List[dict]) -> dict:
    lower = name.lower()
    for entry in profiles:
        pattern = entry.get("pattern")
        if pattern and re.search(pattern, lower):
            return entry
    return profiles[-1] if profiles else {}

def parse_file(cleaned_json: Path, chunk_size: int = 1, profile: dict | None = None) -> Dict:
    data = json.loads(cleaned_json.read_text(encoding="utf-8"))
    title = data.get("title") or cleaned_json.stem
    transcript = data.get("transcript") or []
    turns: List[Dict[str, object]] = []
    profile_name = profile.get("name") if profile else None
    profile_chunks = profile.get("chunk_size") if profile else None
    for ex in transcript:
        speaker = (ex.get("speaker") or "Speaker").strip()
        text = (ex.get("text") or "").strip()
        if not text or is_meta(text):
            continue
        sents = sentence_split(text)
        effective_chunk = profile_chunks if profile_chunks else chunk_size
        chunks = sents if effective_chunk <= 1 else [" ".join(sents[i:i + effective_chunk]).strip() for i in range(0, len(sents), effective_chunk)]
        for chunk in chunks:
            if len(chunk) < 2:
                continue
            turns.append({
                "speaker": speaker,
                "speaker_role": normalize_role(speaker),
                "text": chunk,
                "is_question": is_question(chunk),
                "tokens": tokenize(chunk),
                "turn_index": len(turns),
            })
    return {
        "source": str(cleaned_json),
        "title": title,
        "turns": turns,
        "profile": profile_name or "general",
    }

def main() -> None:
    ap = argparse.ArgumentParser(description="Create parsed, turn-level conversation JSONs")
    ap.add_argument("--input-dir", default="RAWDATA/ConversationClean")
    ap.add_argument("--out-dir", default="RAWDATA/ConversationParsed")
    ap.add_argument("--chunk-size", type=int, default=1)
    ap.add_argument("--profile-map", default="configs/conversation_profiles.json")
    args = ap.parse_args()

    in_dir = Path(args.input_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    profile_map = load_profile_map(Path(args.profile_map))

    files = list(in_dir.glob("*.json"))
    for fp in files:
        try:
            cs = max(1, int(getattr(args, "chunk_size", 1)))
            profile = match_profile(fp.stem, profile_map) if profile_map else {}
            parsed = parse_file(fp, chunk_size=cs, profile=profile)
            out = out_dir / (fp.stem + "_parsed.json")
            out.write_text(json.dumps(parsed, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"Parsed: {fp.name} -> {out.name} (chunk={cs}, profile={parsed.get('profile')}, turns={len(parsed.get('turns'))})")
        except Exception as e:
            print(f"Failed {fp}: {e}")


if __name__ == "__main__":
    main()

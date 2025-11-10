"""Create enriched QA dataset capturing courtroom graph features."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Iterable, List

STOPWORDS = {
    "the", "and", "or", "but", "if", "so", "because", "that", "this",
    "these", "those", "you", "your", "we", "they", "i", "a", "an"
}

QUESTION_KEYWORDS = ["why", "how", "what", "when", "where", "who", "which", "did", "does", "do", "can", "could", "would", "should"]

ROLE_MAP = {
    "justice": "Justice",
    "chief justice": "Justice",
    "justice sotomayor": "Justice",
    "justice gorsuch": "Justice",
    "justice thomas": "Justice",
    "solicitor general": "GovtCounsel",
    "counsel": "Advocate",
    "mr.": "Advocate",
    "ms.": "Advocate",
    "ms": "Advocate",
    "mr": "Advocate",
    "narration": "Narration",
}


def is_question(text: str) -> bool:
    txt = text.strip()
    if not txt:
        return False
    if txt.endswith("?"):
        return True
    lower = txt.lower()
    return any(lower.startswith(keyword + " ") or lower.startswith(keyword + "?") for keyword in QUESTION_KEYWORDS)


def text_tokens(text: str) -> list[str]:
    tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return [t for t in tokens if t not in STOPWORDS]


def compute_overlap(q_tokens: Iterable[str], a_tokens: Iterable[str]) -> float:
    q_set = set(q_tokens)
    a_set = set(a_tokens)
    if not q_set or not a_set:
        return 0.0
    return len(q_set & a_set) / max(1, len(q_set | a_set))


def classify_answer_type(directness_score: float, shift_score: float, answer_text: str) -> str:
    lower = answer_text.lower()
    if directness_score > 0.6:
        return "DirectAnswer"
    if shift_score > 0.6:
        if "deflect" in lower or "question" in lower or "instead" in lower:
            return "Deflect"
        return "PartialAnswer"
    if answer_text.strip().endswith("?") or "?" in lower:
        return "QuestionBack"
    return "PartialAnswer"


def normalize_role(speaker: str) -> str:
    lower = (speaker or "").lower()
    for key, role in ROLE_MAP.items():
        if key in lower:
            return role
    return "Other"


def adjacency_features(turns: List[dict], q_idx: int, a_idx: int) -> int:
    start = max(0, q_idx - 2)
    end = min(len(turns), a_idx + 2)
    speakers = [ (t.get("speaker") or "").strip().lower() for t in turns[start:end] if t.get("speaker") ]
    counts = Counter(speakers)
    return counts.get((turns[q_idx].get("speaker") or "").strip().lower(), 0)


def compute_pairs(turns: list[dict]) -> list[dict]:
    docs = []
    last_question_idx = None
    for idx, turn in enumerate(turns):
        text = (turn.get("text") or "").strip()
        if not text:
            continue
        if is_question(text):
            last_question_idx = idx
            continue
        if last_question_idx is None:
            continue
        question = turns[last_question_idx]
        answer = turn
        q_text = (question.get("text") or "").strip()
        a_text = (answer.get("text") or "").strip()
        q_tokens = text_tokens(q_text)
        a_tokens = text_tokens(a_text)
        directness = compute_overlap(q_tokens, a_tokens)
        shift = round(1.0 - directness, 3)
        answer_type = classify_answer_type(directness, shift, a_text)
        follow_up_flag = False
        follow_up_outcome = "none"
        if idx + 1 < len(turns) and is_question((turns[idx + 1].get("text") or "")):
            follow_up_flag = True
            next_answer = None
            for j in range(idx + 2, len(turns)):
                candidate = turns[j]
                if not is_question((candidate.get("text") or "")):
                    next_answer = candidate
                    break
            if next_answer:
                next_tokens = text_tokens((next_answer.get("text") or "").strip())
                next_directness = compute_overlap(q_tokens, next_tokens)
                follow_up_outcome = "clarified" if next_directness > directness else "deferred"
        doc = {
            "question_turn": last_question_idx,
            "answer_turn": idx,
            "question_speaker": (question.get("speaker") or "unknown").strip(),
            "answer_speaker": (answer.get("speaker") or "unknown").strip(),
            "question_role": normalize_role(question.get("speaker")),
            "answer_role": normalize_role(answer.get("speaker")),
            "question_text": q_text,
            "answer_text": a_text,
            "directness_score": round(directness, 3),
            "topic_shift_score": shift,
            "answer_type": answer_type,
            "follow_up_flag": follow_up_flag,
            "follow_up_outcome": follow_up_outcome,
            "adjacency_weight": adjacency_features(turns, last_question_idx, idx),
        }
        docs.append(doc)
        last_question_idx = None
    return docs


def main() -> None:
    parser = argparse.ArgumentParser(description="Build enriched QA dataset from parsed transcripts")
    parser.add_argument("--input-dir", default="RAWDATA/ConversationParsed")
    parser.add_argument("--output-dir", default="datasets/conversation_rich")
    parser.add_argument("--manifest", default="datasets/conversation_rich/manifest.csv")
    parser.add_argument("--sample", type=int, default=0, help="Limit QA pairs per file")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = Path(args.manifest)
    header = ["file_id", "title", "source", "pairs"]
    if not manifest.exists():
        with manifest.open("w", newline="", encoding="utf-8") as cm:
            csv.DictWriter(cm, fieldnames=header).writeheader()

    for parsed in sorted(input_dir.glob("*_parsed.json")):
        data = json.loads(parsed.read_text(encoding="utf-8"))
        pairs = compute_pairs(data.get("turns") or [])
        if args.sample and len(pairs) > args.sample:
            pairs = pairs[: args.sample]
        out_file = output_dir / f"{parsed.stem}.jsonl"
        with out_file.open("w", encoding="utf-8") as outf:
            for pair in pairs:
                record = {
                    "file_id": parsed.stem,
                    "title": data.get("title"),
                    "source": data.get("source"),
                    **pair,
                }
                outf.write(json.dumps(record, ensure_ascii=False) + "\n")
        with manifest.open("a", newline="", encoding="utf-8") as cm:
            csv.DictWriter(cm, fieldnames=header).writerow({
                "file_id": parsed.stem,
                "title": data.get("title"),
                "source": data.get("source"),
                "pairs": len(pairs),
            })
        print(f"Wrote {len(pairs)} enriched pairs for {parsed.name}")

if __name__ == "__main__":
    main()

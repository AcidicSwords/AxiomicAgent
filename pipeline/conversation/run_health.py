#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Dict

from adapters.conversation.adapter import ConversationAdapter
import re
from collections import Counter


STOPWORDS = set(
    """
    a an and are as at be by for from has have if in into is it of on or our out
    that the their there these they this to was were will with you your i he she we
    not no yes okay ok mm hmm uh um yeah right just really kind sort maybe could would should
    transcript transcripts medium member access subscribe signin sign-in login log-in
    """.split()
)


def _keywords(text: str, top_k: int = 6) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z\-]{2,}", text.lower())
    words = [w for w in words if w not in STOPWORDS and len(w) >= 3]
    counts = Counter(words)
    return [w for w, _ in counts.most_common(top_k)]


def _inflection_points(signals: list[dict], turns: list[dict], window: int = 2) -> list[dict]:
    """Detect conversational inflection points and summarize them in plain content terms.

    Heuristics:
    - Mark a step as an inflection if TED jumps (> 0.48) or continuity drops (< 0.2),
      or if both TED>0.4 and q changes by > 0.3 relative to previous.
    - Summarize content using keywords from a small window of turns around the step.
    """
    out: list[dict] = []
    n = len(signals)
    for i, s in enumerate(signals):
        q = float(s.get("q", 0) or 0)
        ted = float(s.get("TED", 0) or 0)
        cont = float(s.get("continuity", 0) or 0)
        prev = signals[i - 1] if i > 0 else None
        prev_q = float((prev or {}).get("q", 0) or 0)
        prev_ted = float((prev or {}).get("TED", 0) or 0)
        dq = abs(q - prev_q)
        dted = abs(ted - prev_ted)
        reason_flags = []
        if ted > 0.55:
            reason_flags.append("high_TED")
        if cont < 0.18:
            reason_flags.append("low_continuity")
        if ted > 0.42 and dq > 0.3:
            reason_flags.append("q_shift")
        if dted > 0.3:
            reason_flags.append("TED_jump")
        # Require at least two corroborating reasons to reduce over-fire
        if len(reason_flags) < 2:
            continue

        # Gather context text from a small window of turns around i
        left = max(0, i - window)
        right = min(len(turns), i + window + 1)
        ctx_text = " ".join((turns[j]["text"] or "") for j in range(left, right) if j < len(turns))
        kws = _keywords(ctx_text, top_k=6)
        summary = "Shift toward " + ", ".join(kws[:3]) if kws else "Topic shift detected"
        out.append({
            "step_index": int(s.get("step_index", i)),
            "q": q,
            "TED": ted,
            "continuity": cont,
            "reasons": reason_flags,
            "keywords": kws,
            "summary": summary,
        })
    return out


def load_transcript(path: Path) -> List[Dict[str, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    turns = data.get("turns") or data.get("transcript") or []
    out = []
    for t in turns:
        speaker = t.get("speaker") or t.get("role") or "Speaker"
        text = t.get("text") or t.get("content") or ""
        if not text:
            continue
        out.append({"speaker": speaker, "text": text})
    return out


def role_for_index(idx: int) -> str:
    return "user" if idx % 2 == 0 else "assistant"


def process_file(path: Path, window: int) -> Dict:
    adapter = ConversationAdapter(window_size=window)
    turns = load_transcript(path)
    signals = []
    for i, turn in enumerate(turns):
        role = role_for_index(i)
        sig = adapter.process_turn(role=role, text=turn["text"])
        signals.append(sig.to_dict())
    summary = adapter.get_conversation_summary()
    recent = adapter.get_recent_signals(min(10, len(adapter.turns)))
    summary["recent"] = [s.to_dict() for s in recent]

    # Top content nodes (TF-IDF-like): concept > entity > question
    weights = {"concept": 1.0, "entity": 0.7, "question": 0.5}
    convo_fillers = {
        "okay","ok","yeah","uh","um","right","roger","over","copy","affirmative","negative",
        "mm","hmm","mmhmm","alright","well","so","sure"
    }
    text_counts: Counter[str] = Counter()
    df_counts: Counter[str] = Counter()
    type_map: Dict[str, str] = {}
    for t in adapter.turns:
        seen_in_turn: set[str] = set()
        for n in t.nodes:
            if not n.text:
                continue
            key = n.text.strip().lower()
            if key in convo_fillers:
                continue
            w = weights.get(n.type, 0.3)
            text_counts[key] += w
            if key not in type_map:
                type_map[key] = n.type
            seen_in_turn.add(key)
        for key in seen_in_turn:
            df_counts[key] += 1
    # Compute IDF and final scores
    N = max(1, len(adapter.turns))
    scored: list[tuple[str, float]] = []
    for text, tf in text_counts.items():
        df = df_counts.get(text, 1)
        idf = max(0.0, __import__("math").log(N / df))
        scored.append((text, float(tf * (0.5 + idf))))
    scored.sort(key=lambda x: x[1], reverse=True)
    top_nodes = []
    for text, score in scored[:10]:
        top_nodes.append({"text": text, "type": type_map.get(text, "concept"), "score": round(float(score), 3)})
    summary["top_content_nodes"] = top_nodes
    # Inflection analysis with plain-language content cues
    inflections = _inflection_points(signals, turns, window=2)
    summary["inflections"] = inflections
    # QA: zero-node and zero-edge fractions
    zero_nodes = sum(1 for s in signals if (s.get("node_count") or 0) == 0)
    zero_edges = sum(1 for s in signals if (s.get("edge_count") or 0) == 0)
    total = max(1, len(signals))
    summary["qa"] = {
        "total_turns": len(turns),
        "analyzed_steps": len(signals),
        "zero_node_fraction": round(zero_nodes / total, 3),
        "zero_edge_fraction": round(zero_edges / total, 3)
    }
    return {"file": str(path), "summary": summary, "signals": signals}


def main() -> None:
    ap = argparse.ArgumentParser(description="Run conversation health metrics over cleaned transcripts")
    ap.add_argument("--input-dir", default="reports/conversation_clean")
    ap.add_argument("--out-dir", default="reports/conversation_metrics")
    ap.add_argument("--window", type=int, default=6, help="Sliding window size for analysis")
    ap.add_argument("--force", action="store_true", help="Recompute even if output is up-to-date")
    args = ap.parse_args()

    in_dir = Path(args.input_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    files = list(in_dir.glob("*.json"))
    bad_dir = in_dir / "Bad"
    if bad_dir.exists():
        files += list(bad_dir.glob("*.json"))
    files = sorted(files, key=lambda p: p.name.lower())

    print(f"[health] Scanning {in_dir} -> {out_dir} (files={len(files)})", flush=True)
    results_index = []
    for i, fp in enumerate(files, 1):
        out_file = out_dir / (fp.stem + ".metrics.json")
        try:
            if out_file.exists() and not args.force:
                try:
                    if out_file.stat().st_mtime >= fp.stat().st_mtime:
                        print(f"[health] [{i}/{len(files)}] Skip up-to-date {out_file.name}", flush=True)
                        continue
                except Exception:
                    pass
            print(f"[health] [{i}/{len(files)}] Analyzing {fp.name} (window={args.window})...", flush=True)
            result = process_file(fp, args.window)
            out_file.write_text(json.dumps(result, indent=2), encoding="utf-8")
            results_index.append({"file": str(fp), "out": str(out_file), **result["summary"]})
            print(f"[health] [{i}/{len(files)}] Wrote {out_file.name}", flush=True)
        except Exception as e:
            print(f"[health] [{i}/{len(files)}] Failed {fp.name}: {e}", flush=True)

    (out_dir / "index.json").write_text(json.dumps(results_index, indent=2), encoding="utf-8")
    print(f"[health] Completed. Wrote index.json with {len(results_index)} entries.", flush=True)


if __name__ == "__main__":
    main()

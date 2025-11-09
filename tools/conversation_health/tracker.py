"""
Lightweight Conversation Health Tracker (Optional Add-on)

Implements a prompt-aligned, context-aware tracker that computes
turn-level heuristics and (optionally) a question->response drift
metric using sentence-transformers, if available.

This module is self-contained and safe to import. It does not change
existing pipeline behavior. Callers opt-in explicitly.
"""

from __future__ import annotations

import time
import re
from collections import deque
from dataclasses import dataclass
from typing import List, Optional, Dict

try:
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover - optional
    np = None  # Fallback when numpy is unavailable

_sentence_model = None  # Lazy singleton


def _get_sentence_model():  # pragma: no cover - optional path
    global _sentence_model
    if _sentence_model is not None:
        return _sentence_model or None
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
        _sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
    except Exception:
        _sentence_model = False
    return _sentence_model or None


@dataclass
class Turn:
    speaker: str
    text: str
    timestamp: float
    is_question: bool
    substantive_sentences: int
    char_count: int
    topics: List[str]


class ConversationHealthTracker:
    """Context-aware, turn-level conversation health assessment."""

    DRIFT_THRESHOLDS = {
        "accountability": 0.30,
        "exploration": 0.70,
        "crisis": 0.40,
        "teaching": 0.50,
        "decision": 0.45,
        "general": 0.60,
    }

    EXPECTED_RANGES = {
        "accountability": {"q": (0.6, 0.8), "ted": (0.0, 0.5)},
        "exploration": {"q": (0.45, 0.55), "ted": (0.7, 0.8)},
        "crisis": {"q": (0.5, 0.6), "ted": (0.4, 0.6)},
        "teaching": {"q": (0.5, 0.7), "ted": (0.5, 0.7)},
        "decision": {"q": (0.55, 0.75), "ted": (0.3, 0.6)},
        "general": {"q": (0.5, 0.7), "ted": (0.4, 0.7)},
    }

    def __init__(self, window_size: int = 10) -> None:
        self.turns: deque[Turn] = deque(maxlen=window_size)
        self.context_type: Optional[str] = None
        self.turn_count = 0
        self.question_count = 0

    # Public API -----------------------------------------------------------

    def add_turn(self, speaker: str, text: str) -> Dict:
        turn = Turn(
            speaker=speaker,
            text=text or "",
            timestamp=time.time(),
            is_question=self._is_question(text or ""),
            substantive_sentences=self._count_substantive_sentences(text or ""),
            char_count=len(text or ""),
            topics=self._extract_topics(text or ""),
        )
        self.turns.append(turn)
        self.turn_count += 1
        if turn.is_question:
            self.question_count += 1
        if speaker == "user":
            self.context_type = self._classify_context(text or "")
        return self.compute_health()

    def compute_health(self) -> Dict:
        out: Dict[str, object] = {
            "context": self.context_type or "general",
            "turn_count": self.turn_count,
            "alerts": [],
            "guidance": [],
            "status": "ok",
        }

        # Compute drift_on_specifics for most recent Q->A if available
        q_text = self._last_question_text()
        a_text = self._last_answer_text()
        drift = self._compute_drift_on_specifics(q_text, a_text)
        if drift is not None:
            out["drift_on_specifics"] = drift
            thresh = self.DRIFT_THRESHOLDS.get(self.context_type or "general", 0.6)
            if drift > thresh:
                out["status"] = "drift_detected"
                out["alerts"].append(
                    f"Response drift {drift:.2f} exceeds {thresh:.2f} for {self.context_type or 'general'} context"
                )

        # Fragmentation: rapid, shallow exchanges heuristic
        frag = self._compute_fragmentation()
        out.update(frag)
        if frag.get("fragmented"):
            out["status"] = "degraded_fragmented"
            out["alerts"].append("Conversation becoming fragmented/shallow")

        # Topic coherence (simple diversity over recent turns)
        coh = self._topic_coherence()
        if coh is not None:
            out["topic_coherence"] = coh
            if coh < 0.3 and (self.context_type or "general") != "exploration":
                out["status"] = "scattered"
                out["alerts"].append("Topics scattering; restore focus")

        return out

    # Internals -----------------------------------------------------------

    def _is_question(self, text: str) -> bool:
        if "?" in text:
            return True
        interrogatives = [
            "why",
            "how",
            "what",
            "when",
            "where",
            "who",
            "which",
            "can you",
            "could you",
            "would you",
        ]
        tl = text.lower().strip()
        return any(tl.startswith(w) for w in interrogatives)

    def _count_substantive_sentences(self, text: str) -> int:
        sentences = re.split(r"[.!?]+", text)
        return sum(1 for s in sentences if len(s.strip()) > 20)

    def _extract_topics(self, text: str) -> List[str]:
        words = re.findall(r"\b[A-Z][a-z]+\b", text)
        stop = {"The", "This", "That", "These", "Those", "A", "An", "I", "You", "We", "They"}
        topics = [w for w in words if w not in stop]
        # Deduplicate, cap length
        seen: set[str] = set()
        out: List[str] = []
        for w in topics:
            if w not in seen:
                out.append(w)
                seen.add(w)
            if len(out) >= 5:
                break
        return out

    def _classify_context(self, user_msg: str) -> str:
        ul = user_msg.lower()
        crisis = ["urgent", "critical", "broken", "not working", "failing", "error", "help"]
        if any(s in ul for s in crisis):
            return "crisis"
        accountability = ["why did", "explain why", "you said", "justify", "how could", "what made you"]
        if any(s in ul for s in accountability):
            return "accountability"
        precision = ["exactly", "specifically", "precisely", "need to be sure", "confirm"]
        if any(s in ul for s in precision):
            return "accountability"
        exploration = ["what if", "maybe", "wondering", "thinking about", "could we", "exploring"]
        if any(s in ul for s in exploration):
            return "exploration"
        teaching = ["how does", "what is", "explain", "i don't understand", "show me"]
        if any(s in ul for s in teaching):
            return "teaching"
        decision = ["should i", "which approach", "help me decide", "recommend", "better"]
        if any(s in ul for s in decision):
            return "decision"
        return "general"

    def _last_question_text(self) -> Optional[str]:
        for t in reversed(self.turns):
            if t.speaker == "user" and t.is_question:
                return t.text
        return None

    def _last_answer_text(self) -> Optional[str]:
        # most recent assistant turn
        for t in reversed(self.turns):
            if t.speaker == "assistant":
                return t.text
        return None

    def _compute_drift_on_specifics(self, question: Optional[str], response: Optional[str]) -> Optional[float]:
        if not question or not response or np is None:
            return None
        model = _get_sentence_model()
        if model is None:
            return None
        q_core = self._extract_interrogative_core(question)
        r_first = self._extract_first_substantive(response)
        if not q_core or not r_first:
            return None
        q_emb = model.encode(q_core)
        r_emb = model.encode(r_first)
        denom = (float(np.linalg.norm(q_emb)) * float(np.linalg.norm(r_emb))) or 1.0
        sim = float(np.dot(q_emb, r_emb)) / denom
        return float(1.0 - sim)

    def _extract_interrogative_core(self, question: str) -> str:
        text = question.lower()
        for filler in ["i was wondering", "could you", "can you", "would you", "please"]:
            text = text.replace(filler, "")
        sentences = re.split(r"[.!?]+", text)
        core = sentences[0].strip() if sentences else text.strip()
        return core or question

    def _extract_first_substantive(self, response: str, min_len: int = 30) -> str:
        for sent in re.split(r"[.!?]+", response):
            if len(sent.strip()) >= min_len:
                return sent.strip()
        return response[:100].strip()

    def _compute_fragmentation(self) -> Dict[str, object]:
        if len(self.turns) < 4:
            return {"fragmented": False}
        recent = list(self.turns)[-4:]
        shallow = sum(1 for t in recent if t.substantive_sentences <= 1)
        fragmented = shallow >= 3
        return {"fragmented": fragmented}

    def _topic_coherence(self) -> Optional[float]:
        if len(self.turns) < 5:
            return None
        recent = list(self.turns)[-5:]
        bag: List[str] = []
        for t in recent:
            bag.extend(t.topics)
        if not bag:
            return None
        uniq = len(set(bag))
        total = len(bag)
        return float(1.0 - (uniq / total))


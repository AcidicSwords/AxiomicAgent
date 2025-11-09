"""
Lightweight Conversation Health Tracker for Claude Code
Implements Tier 2 system with turn-level metrics and context-aware guidance.

Based on:
- TURN_LEVEL_METRICS_PROPOSAL.md
- REALISTIC_IMPLEMENTATION_PLAN.md
- CLAUDE_CODE_CONVERSATION_REASONING_PROMPT.md
"""

import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

import time
import re
from collections import deque
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple
import numpy as np

# Lazy import of sentence transformer (only when needed)
_sentence_model = None

def get_sentence_model():
    """Lazy-load sentence transformer model."""
    global _sentence_model
    if _sentence_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
            print("✓ Loaded sentence transformer model")
        except ImportError:
            print("⚠ sentence-transformers not installed. Install with: pip install sentence-transformers")
            _sentence_model = False
    return _sentence_model if _sentence_model is not False else None


@dataclass
class Turn:
    """Represents a single conversation turn."""
    speaker: str
    text: str
    timestamp: float
    is_question: bool
    substantive_sentences: int
    char_count: int
    topics: List[str]


@dataclass
class TurnMetrics:
    """Metrics computed for a turn pair (question -> response)."""
    drift_on_specifics: Optional[float]  # Semantic drift from Q to A
    response_directness: float  # 0-1, how directly question was addressed
    substantive_content: bool  # Whether response has depth


class ConversationHealthTracker:
    """
    Track conversation patterns in real-time.
    Implements lightweight state tracking without full graph computation.
    """

    # Context-dependent drift thresholds
    DRIFT_THRESHOLDS = {
        'accountability': 0.30,   # Direct answers needed (Prince Andrew pattern)
        'exploration': 0.70,      # Open-ended, drift OK (Rogers-Gloria pattern)
        'crisis': 0.40,           # Stay focused (Apollo 13 pattern)
        'teaching': 0.50,         # Clarify but allow examples
        'decision': 0.45,         # Balance options with focus
        'general': 0.60,          # Default moderate
    }

    # Expected metric ranges by context
    EXPECTED_RANGES = {
        'accountability': {'q': (0.6, 0.8), 'ted': (0.0, 0.5)},
        'exploration': {'q': (0.45, 0.55), 'ted': (0.7, 0.8)},
        'crisis': {'q': (0.5, 0.6), 'ted': (0.4, 0.6)},
        'teaching': {'q': (0.5, 0.7), 'ted': (0.5, 0.7)},
        'decision': {'q': (0.55, 0.75), 'ted': (0.3, 0.6)},
        'general': {'q': (0.5, 0.7), 'ted': (0.4, 0.7)},
    }

    def __init__(self, window_size: int = 10):
        """
        Initialize tracker.

        Args:
            window_size: Number of recent turns to track (sliding window)
        """
        self.turns = deque(maxlen=window_size)
        self.context_type: Optional[str] = None
        self.turn_count = 0
        self.question_count = 0
        self.drift_violations = 0

    def add_turn(self, speaker: str, text: str) -> Dict:
        """
        Add new turn and compute metrics.

        Args:
            speaker: Who is speaking (user/assistant)
            text: The message content

        Returns:
            Health metrics and guidance
        """
        turn = Turn(
            speaker=speaker,
            text=text,
            timestamp=time.time(),
            is_question=self._is_question(text),
            substantive_sentences=self._count_substantive_sentences(text),
            char_count=len(text),
            topics=self._extract_topics(text)
        )

        self.turns.append(turn)
        self.turn_count += 1

        if turn.is_question:
            self.question_count += 1

        # Update context classification
        if speaker == 'user':
            self.context_type = self._classify_context(text)

        return self.compute_health()

    def _is_question(self, text: str) -> bool:
        """Check if text contains a question."""
        # Direct question mark
        if '?' in text:
            return True

        # Interrogative words
        interrogatives = ['why', 'how', 'what', 'when', 'where', 'who', 'which', 'can you', 'could you', 'would you']
        text_lower = text.lower()
        return any(text_lower.startswith(word) for word in interrogatives)

    def _count_substantive_sentences(self, text: str) -> int:
        """Count sentences with actual content (>20 chars)."""
        sentences = re.split(r'[.!?]+', text)
        return sum(1 for s in sentences if len(s.strip()) > 20)

    def _extract_topics(self, text: str) -> List[str]:
        """Simple topic extraction via capitalized words."""
        words = re.findall(r'\b[A-Z][a-z]+\b', text)
        # Filter common words
        stopwords = {'The', 'This', 'That', 'These', 'Those', 'A', 'An', 'I', 'You', 'We', 'They'}
        topics = [w for w in words if w not in stopwords]
        return list(set(topics))[:5]  # Top 5 unique

    def _classify_context(self, user_msg: str) -> str:
        """Classify conversation context from user signals."""
        user_lower = user_msg.lower()

        # Crisis/urgent signals (highest priority)
        crisis_signals = ['urgent', 'critical', 'broken', 'not working', 'failing', 'error', 'help']
        if any(signal in user_lower for signal in crisis_signals):
            return 'crisis'

        # Accountability signals
        accountability_signals = ['why did', 'explain why', 'you said', 'justify', 'how could', 'what made you']
        if any(signal in user_lower for signal in accountability_signals):
            return 'accountability'

        # Precision signals
        precision_signals = ['exactly', 'specifically', 'precisely', 'need to be sure', 'confirm']
        if any(signal in user_lower for signal in precision_signals):
            return 'accountability'  # Treat as accountability

        # Exploration signals
        exploration_signals = ['what if', 'maybe', 'wondering', 'thinking about', 'could we', 'exploring']
        if any(signal in user_lower for signal in exploration_signals):
            return 'exploration'

        # Teaching signals
        teaching_signals = ['how does', 'what is', 'explain', 'i don\'t understand', 'show me']
        if any(signal in user_lower for signal in teaching_signals):
            return 'teaching'

        # Decision signals
        decision_signals = ['should i', 'which approach', 'help me decide', 'recommend', 'better']
        if any(signal in user_lower for signal in decision_signals):
            return 'decision'

        return 'general'

    def compute_drift_on_specifics(self, question: str, response: str) -> Optional[float]:
        """
        Compute semantic drift between question and immediate response.
        This is the core turn-level metric from the proposal.
        """
        model = get_sentence_model()
        if model is None:
            return None

        # Extract interrogative core from question
        q_core = self._extract_interrogative_core(question)

        # Extract first substantive content from response
        r_first = self._extract_first_substantive(response)

        if not q_core or not r_first:
            return None

        # Compute semantic similarity
        q_emb = model.encode(q_core)
        r_emb = model.encode(r_first)

        similarity = np.dot(q_emb, r_emb) / (np.linalg.norm(q_emb) * np.linalg.norm(r_emb))
        drift = 1.0 - similarity  # Convert similarity to drift

        return float(drift)

    def _extract_interrogative_core(self, question: str) -> str:
        """Extract the core question being asked."""
        # Remove filler phrases
        fillers = ['i was wondering', 'could you', 'can you', 'would you', 'please']
        text = question.lower()
        for filler in fillers:
            text = text.replace(filler, '')

        # Get first sentence if multiple
        sentences = re.split(r'[.!?]+', text)
        core = sentences[0].strip() if sentences else text.strip()

        return core or question  # Fallback to original

    def _extract_first_substantive(self, response: str, min_length: int = 30) -> str:
        """Extract first substantive sentence from response."""
        sentences = re.split(r'[.!?]+', response)

        for sentence in sentences:
            if len(sentence.strip()) >= min_length:
                return sentence.strip()

        # Fallback: first 100 chars if no substantive sentence found
        return response[:100]

    def compute_fragmentation_metrics(self) -> Dict:
        """
        Compute conversation fragmentation metrics.
        Implements interruption_rate and min_substantive_turn_len from proposal.
        """
        if len(self.turns) < 3:
            return {
                'interruption_rate': 0.0,
                'avg_substantive': 0.0,
                'avg_turn_length': 0,
                'fragmented': False
            }

        recent = list(self.turns)[-10:]  # Last 10 turns

        # Metric 1: Interruption rate (rapid-fire exchanges <5s apart)
        interruptions = 0
        for i in range(1, len(recent)):
            time_gap = recent[i].timestamp - recent[i-1].timestamp
            if time_gap < 5.0:
                interruptions += 1

        interruption_rate = interruptions / (len(recent) - 1) if len(recent) > 1 else 0.0

        # Metric 2: Average substantive content
        avg_substantive = sum(t.substantive_sentences for t in recent) / len(recent)

        # Metric 3: Average turn length
        avg_turn_length = sum(t.char_count for t in recent) / len(recent)

        # Health assessment
        fragmented = (interruption_rate > 0.6 and avg_turn_length < 100) or avg_substantive < 1.0

        return {
            'interruption_rate': interruption_rate,
            'avg_substantive': avg_substantive,
            'avg_turn_length': avg_turn_length,
            'fragmented': fragmented
        }

    def compute_health(self) -> Dict:
        """
        Compute overall conversation health.
        Returns metrics and guidance.
        """
        if len(self.turns) < 2:
            return {
                'status': 'warming_up',
                'context': self.context_type or 'general',
                'guidance': 'Continue conversation naturally'
            }

        health = {
            'status': 'healthy',
            'context': self.context_type or 'general',
            'turn_count': self.turn_count,
            'alerts': [],
            'guidance': []
        }

        # Check for question-response drift (if we have a recent Q->A pair)
        recent_turns = list(self.turns)[-2:]
        if len(recent_turns) == 2 and recent_turns[0].is_question and recent_turns[1].speaker != recent_turns[0].speaker:
            question = recent_turns[0].text
            response = recent_turns[1].text

            drift = self.compute_drift_on_specifics(question, response)
            if drift is not None:
                health['drift_on_specifics'] = drift

                # Check against context threshold
                threshold = self.DRIFT_THRESHOLDS.get(self.context_type, 0.6)
                if drift > threshold:
                    self.drift_violations += 1
                    health['status'] = 'drift_detected'
                    health['alerts'].append(
                        f"DRIFT ALERT: Response drift {drift:.2f} exceeds {threshold:.2f} for {self.context_type} context"
                    )
                    health['guidance'].append(self._get_drift_guidance(drift, threshold))

        # Check fragmentation
        frag = self.compute_fragmentation_metrics()
        health.update(frag)

        if frag['fragmented']:
            health['status'] = 'degraded_fragmented'
            health['alerts'].append("FRAGMENTATION: Conversation becoming scattered")
            health['guidance'].append(
                "Slow down. Consolidate topics. Ask 'Does this make sense?' before proceeding."
            )

        # Topic coherence check
        if len(self.turns) >= 5:
            recent_topics = []
            for turn in list(self.turns)[-5:]:
                recent_topics.extend(turn.topics)

            unique_topics = len(set(recent_topics))
            total_mentions = len(recent_topics)

            if total_mentions > 0:
                coherence = 1.0 - (unique_topics / total_mentions)
                health['topic_coherence'] = coherence

                if coherence < 0.3 and self.context_type != 'exploration':
                    health['status'] = 'scattered'
                    health['alerts'].append("COHERENCE: Topics scattering")
                    health['guidance'].append(
                        "Return to core topic. Summarize progress before shifting focus."
                    )

        return health

    def _get_drift_guidance(self, drift: float, threshold: float) -> str:
        """Generate context-specific guidance for drift violation."""
        context = self.context_type or 'general'

        if context == 'accountability':
            return (
                f"Expected: Direct answers to specific questions\n"
                f"Action: Return to user's question, answer specifically first\n"
                f"PATTERN MATCH: Prince Andrew evasion pattern detected"
            )
        elif context == 'crisis':
            return (
                f"Crisis mode: Prioritize clarity and directness\n"
                f"Action: State facts explicitly, offer immediate actionable help\n"
                f"PATTERN MATCH: Apollo 13 precision protocol needed"
            )
        elif context == 'teaching':
            return (
                f"Teaching context: Ensure you're addressing the core confusion\n"
                f"Action: Verify understanding before expanding\n"
                f"Ask: 'Does this answer your question about [X]?'"
            )
        else:
            return (
                f"Response may not be addressing user's question directly\n"
                f"Action: Re-read question, provide specific answer first"
            )

    def generate_coaching_summary(self) -> str:
        """
        Generate coaching guidance based on conversation patterns.
        This is what would appear in Claude Code context.
        """
        if len(self.turns) < 3:
            return "[Conversation too short for coaching]"

        health = self.compute_health()
        context = health['context']
        expected = self.EXPECTED_RANGES.get(context, self.EXPECTED_RANGES['general'])

        lines = []
        lines.append(f"=== CONVERSATION HEALTH ===")
        lines.append(f"Context: {context.upper()}")
        lines.append(f"Status: {health['status']}")
        lines.append(f"Turns: {health['turn_count']}")
        lines.append("")

        # Expected ranges for this context
        lines.append(f"Expected ranges for {context}:")
        lines.append(f"  Quality (q): {expected['q'][0]:.2f} - {expected['q'][1]:.2f}")
        lines.append(f"  Drift (TED): {expected['ted'][0]:.2f} - {expected['ted'][1]:.2f}")
        lines.append(f"  Max question->response drift: {self.DRIFT_THRESHOLDS[context]:.2f}")
        lines.append("")

        # Current metrics
        if 'drift_on_specifics' in health:
            lines.append(f"Current question->response drift: {health['drift_on_specifics']:.2f}")

        if 'topic_coherence' in health:
            lines.append(f"Topic coherence: {health['topic_coherence']:.2f}")

        lines.append(f"Fragmentation: {'YES' if health.get('fragmented') else 'NO'}")
        lines.append("")

        # Alerts
        if health['alerts']:
            lines.append("ALERTS:")
            for alert in health['alerts']:
                lines.append(f"  ⚠ {alert}")
            lines.append("")

        # Guidance
        if health['guidance']:
            lines.append("GUIDANCE:")
            for guide in health['guidance']:
                lines.append(f"  → {guide}")
        else:
            lines.append("✓ Conversation health is good. Continue current approach.")

        return "\n".join(lines)


def example_integration_hook(user_msg: str, assistant_msg: str, tracker: ConversationHealthTracker) -> Optional[str]:
    """
    Example hook for Claude Code integration.
    This would be called after each assistant response.

    Returns guidance to inject into next context, or None if conversation is healthy.
    """
    # Add user turn
    tracker.add_turn('user', user_msg)

    # Add assistant turn
    health = tracker.add_turn('assistant', assistant_msg)

    # Only inject guidance if there are alerts
    if health.get('alerts'):
        return tracker.generate_coaching_summary()

    return None


# Example usage and testing
if __name__ == "__main__":
    print("Conversation Health Tracker - Tier 2 Implementation")
    print("=" * 80)
    print()

    tracker = ConversationHealthTracker()

    # Simulate a conversation with evasion pattern (Prince Andrew style)
    print("TEST 1: Accountability Evasion Pattern")
    print("-" * 80)

    user_msg = "Why did the authentication system fail on production?"
    assistant_msg = "Authentication is an important aspect of modern applications. There are many approaches to handling auth, including OAuth, JWT tokens, and session-based systems. Let me explain the different options..."

    guidance = example_integration_hook(user_msg, assistant_msg, tracker)
    print(f"User: {user_msg}")
    print(f"Assistant: {assistant_msg[:100]}...")
    print()
    if guidance:
        print("GUIDANCE GENERATED:")
        print(guidance)
    print()
    print()

    # Simulate healthy exploration (Rogers-Gloria style)
    print("TEST 2: Healthy Exploration Pattern")
    print("-" * 80)

    tracker2 = ConversationHealthTracker()

    user_msg2 = "I'm wondering if we should refactor this architecture... maybe microservices? Or perhaps just modularize the monolith?"
    assistant_msg2 = "Let's explore both paths. With microservices, you'd gain deployment independence and team autonomy. The trade-off is complexity. With a modularized monolith, you keep simplicity but might face scaling challenges later. What matters more to your team right now - independence or simplicity?"

    guidance2 = example_integration_hook(user_msg2, assistant_msg2, tracker2)
    print(f"User: {user_msg2}")
    print(f"Assistant: {assistant_msg2[:100]}...")
    print()
    if guidance2:
        print("GUIDANCE GENERATED:")
        print(guidance2)
    else:
        print("✓ No alerts - healthy exploration detected")
    print()
    print()

    # Simulate crisis (Apollo 13 style)
    print("TEST 3: Crisis Pattern")
    print("-" * 80)

    tracker3 = ConversationHealthTracker()

    user_msg3 = "URGENT: Production database is throwing connection errors"
    assistant_msg3 = "I can help troubleshoot. First, let me explain how database connections work in general..."

    guidance3 = example_integration_hook(user_msg3, assistant_msg3, tracker3)
    print(f"User: {user_msg3}")
    print(f"Assistant: {assistant_msg3[:100]}...")
    print()
    if guidance3:
        print("GUIDANCE GENERATED:")
        print(guidance3)

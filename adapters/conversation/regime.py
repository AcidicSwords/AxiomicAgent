"""
Regime classification for conversations.
"""

from typing import List
from .types import ConversationSignals, RegimeClassification


class RegimeClassifier:
    """
    Classify conversation state into regimes.

    Based on (q, TED, continuity) signatures.
    """

    def classify(self, signals: ConversationSignals) -> RegimeClassification:
        """
        Classify current conversation regime.

        Returns RegimeClassification with regime type and confidence.
        """
        q = signals.q
        ted = signals.TED
        cont = signals.continuity
        spread = signals.spread or 0.5

        # Stuck: Premature convergence
        if q > 0.80 and ted < 0.15 and cont > 0.65:
            return RegimeClassification(
                regime="stuck",
                confidence=0.9,
                signals=signals,
                warning="Premature convergence detected",
                recommendations=[
                    "Inject divergence: explore alternative perspectives",
                    "Ask 'what if' questions",
                    "Sample mid-distance topics (2-3 hops away)"
                ]
            )

        # Scattered: Too chaotic
        if q < 0.50 and ted > 0.45 and spread > 0.6:
            return RegimeClassification(
                regime="scattered",
                confidence=0.85,
                signals=signals,
                warning="Conversation fragmented across topics",
                recommendations=[
                    "Identify common threads",
                    "Build bridging connections",
                    "Synthesize main points"
                ]
            )

        # Exploring: Healthy learning zone
        if 0.55 < q < 0.85 and 0.20 < ted < 0.40 and 0.3 < cont < 0.6:
            return RegimeClassification(
                regime="exploring",
                confidence=0.8,
                signals=signals,
                status="Optimal learning zone",
                recommendations=[
                    "Continue current approach",
                    "Monitor for saturation or convergence"
                ]
            )

        # Deep dive: Sustained focus
        if q > 0.75 and 0.10 < ted < 0.25 and cont > 0.55 and spread < 0.3:
            return RegimeClassification(
                regime="deep_dive",
                confidence=0.75,
                signals=signals,
                status="Sustained deep focus",
                recommendations=[
                    "Maintain depth",
                    "Watch for diminishing returns (stuck)"
                ]
            )

        # Pivot: Major transition
        if ted > 0.50 and 0.2 < cont < 0.5:
            return RegimeClassification(
                regime="pivot",
                confidence=0.7,
                signals=signals,
                status="Topic transition detected",
                recommendations=[
                    "Acknowledge the shift",
                    "Build bridge to prior context",
                    "Clarify new direction"
                ]
            )

        # Default: Mixed/unclear
        return RegimeClassification(
            regime="mixed",
            confidence=0.5,
            signals=signals,
            status="No clear pattern",
            recommendations=["Continue observing"]
        )

    def detect_trends(self, signal_history: List[ConversationSignals]) -> dict:
        """
        Detect trends across multiple turns.

        Returns trend analysis.
        """
        if len(signal_history) < 3:
            return {"trend": "insufficient_data"}

        # Extract recent values
        recent_q = [s.q for s in signal_history[-5:]]
        recent_ted = [s.TED for s in signal_history[-5:] if s.TED is not None]

        trends = {}

        # Q trend
        if len(recent_q) >= 3:
            if recent_q[-1] > recent_q[-3] + 0.1:
                trends["q_trend"] = "increasing"  # Converging
            elif recent_q[-1] < recent_q[-3] - 0.1:
                trends["q_trend"] = "decreasing"  # Fragmenting
            else:
                trends["q_trend"] = "stable"

        # TED trend
        if len(recent_ted) >= 3:
            if recent_ted[-1] > recent_ted[-3] + 0.1:
                trends["TED_trend"] = "increasing"  # Diverging
            elif recent_ted[-1] < recent_ted[-3] - 0.1:
                trends["TED_trend"] = "decreasing"  # Stabilizing
            else:
                trends["TED_trend"] = "stable"

        # Detect oscillation (healthy)
        if len(recent_ted) >= 4:
            # Check if TED alternates high/low
            oscillating = False
            for i in range(len(recent_ted) - 2):
                if (recent_ted[i] < 0.3 and recent_ted[i+1] > 0.3) or \
                   (recent_ted[i] > 0.3 and recent_ted[i+1] < 0.3):
                    oscillating = True
                    break

            if oscillating:
                trends["pattern"] = "oscillating"  # Healthy exploration
            elif all(t < 0.2 for t in recent_ted[-3:]):
                trends["pattern"] = "stuck"  # Stagnant
            elif all(t > 0.4 for t in recent_ted[-3:]):
                trends["pattern"] = "chaotic"  # Too much change

        return trends


class ClaudeBehaviorAnalyzer:
    """
    Analyze Claude-specific response patterns.

    Detects when Claude exhibits failure modes.
    """

    def analyze_response(self, text: str, signals: ConversationSignals) -> dict:
        """
        Analyze Claude's response characteristics.

        Returns behavioral pattern analysis.
        """
        patterns = {}

        # 1. Hedge density (epistemic uncertainty)
        hedge_words = ["might", "could", "possibly", "perhaps", "seems", "likely", "may"]
        word_count = len(text.split())
        hedge_count = sum(text.lower().count(h) for h in hedge_words)
        patterns["hedge_density"] = hedge_count / word_count if word_count > 0 else 0

        # 2. Acknowledgment patterns (active listening)
        ack_patterns = [
            "you mentioned", "you asked", "you're right", "i see",
            "that's a good point", "as you noted", "you're correct"
        ]
        patterns["has_acknowledgment"] = any(
            p in text.lower() for p in ack_patterns
        )

        # 3. Meta-commentary (thinking about thinking)
        meta_patterns = [
            "let me", "i'll", "first", "to clarify", "breaking this down",
            "in other words", "thinking about", "before we"
        ]
        patterns["meta_commentary"] = any(
            p in text.lower() for p in meta_patterns
        )

        # 4. Question density (exploration)
        questions = text.count("?")
        sentences = len([s for s in text.split(".") if s.strip()])
        patterns["question_density"] = questions / sentences if sentences > 0 else 0

        # 5. Structure markers (organization)
        structure_markers = [
            "first", "second", "third", "finally",
            "however", "therefore", "additionally",
            "in contrast", "on the other hand"
        ]
        patterns["structure_markers"] = sum(
            1 for m in structure_markers if m in text.lower()
        )

        return patterns

    def detect_failure_modes(self, patterns: dict, signals: ConversationSignals) -> List[dict]:
        """
        Detect Claude failure modes.

        Returns list of detected failures.
        """
        failures = []

        # Overconfident: Low hedges + high certainty
        if patterns["hedge_density"] < 0.01 and signals.q > 0.9:
            failures.append({
                "type": "overconfident",
                "severity": "medium",
                "description": "High certainty without hedging - may be premature"
            })

        # Circular: High continuity + low TED
        if signals.continuity > 0.8 and signals.TED < 0.10:
            failures.append({
                "type": "circular",
                "severity": "high",
                "description": "Repeating same concepts without progress"
            })

        # Scattered questions: Many questions + low q
        if patterns["question_density"] > 0.3 and signals.q < 0.5:
            failures.append({
                "type": "scattered_exploration",
                "severity": "medium",
                "description": "Asking questions without synthesis"
            })

        # Robotic: High structure but no acknowledgment
        if patterns["structure_markers"] > 5 and not patterns["has_acknowledgment"]:
            failures.append({
                "type": "robotic",
                "severity": "low",
                "description": "Overly structured, lacks engagement"
            })

        return failures

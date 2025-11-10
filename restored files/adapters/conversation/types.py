"""
Type definitions for conversation adapter.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
import numpy as np


@dataclass
class ConversationNode:
    """
    A node in the conversation graph.

    Represents concepts, claims, questions, or entities mentioned.
    """
    id: str
    text: str
    type: str  # "concept", "claim", "question", "entity", "acknowledgment"
    role: str  # "user" or "assistant"
    embedding: np.ndarray
    turn_index: int
    metadata: Dict = field(default_factory=dict)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if not isinstance(other, ConversationNode):
            return False
        return self.id == other.id


@dataclass
class ConversationEdge:
    """
    An edge in the conversation graph.

    Represents relationships between concepts/claims.
    """
    source: str  # Node ID
    target: str  # Node ID
    type: str  # "co-mention", "reply", "support", "elaboration"
    weight: float
    quality: float  # q(e) ∈ [0,1]
    turn_index: int
    metadata: Dict = field(default_factory=dict)


@dataclass
class ConversationTurn:
    """
    A single turn in the conversation.
    """
    turn_index: int
    role: str  # "user" or "assistant"
    text: str
    nodes: List[ConversationNode] = field(default_factory=list)
    edges: List[ConversationEdge] = field(default_factory=list)
    timestamp: Optional[str] = None
    metadata: Dict = field(default_factory=dict)

    def node_ids(self) -> Set[str]:
        """Get set of node IDs in this turn."""
        return {n.id for n in self.nodes}

    def concept_texts(self) -> Set[str]:
        """Get set of concept texts (normalized)."""
        return {n.text.lower() for n in self.nodes}


@dataclass
class ConversationSignals:
    """
    Computed signals for a conversation step.

    Compatible with core/signals.py output format.
    """
    step_index: int
    q: float  # Quality/coherence
    TED: float  # Drift from previous step
    continuity: float  # Overlap with previous step
    spread: Optional[float] = None  # Topic dispersion
    ted_trusted: Optional[float] = None  # Reliability-weighted drift
    node_count: int = 0
    edge_count: int = 0
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary for reporting."""
        return {
            "step_index": int(self.step_index),
            "q": float(round(self.q, 3)),
            "TED": float(round(self.TED, 3)),
            "continuity": float(round(self.continuity, 3)),
            "spread": float(round(self.spread, 3)) if self.spread is not None else None,
            "ted_trusted": float(round(self.ted_trusted, 3)) if self.ted_trusted is not None else None,
            "node_count": int(self.node_count),
            "edge_count": int(self.edge_count),
            **self.metadata
        }


@dataclass
class RegimeClassification:
    """
    Regime classification for conversation state.
    """
    regime: str  # "stuck", "exploring", "scattered", "deep_dive", "pivot"
    confidence: float
    signals: ConversationSignals
    warning: Optional[str] = None
    status: Optional[str] = None
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary for reporting."""
        return {
            "regime": self.regime,
            "confidence": round(self.confidence, 3),
            "warning": self.warning,
            "status": self.status,
            "recommendations": self.recommendations,
            "signals": self.signals.to_dict()
        }

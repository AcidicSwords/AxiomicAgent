from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(slots=True)
class ConversationNode:
    id: str
    text: str
    type: str
    role: str
    turn_index: int
    embedding: List[float] = field(default_factory=lambda: [0.0])
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ConversationEdge:
    source: str
    target: str
    type: str = "adjacency"
    weight: float = 1.0
    quality: float | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ConversationTurn:
    turn_index: int
    role: str
    text: str
    nodes: List[ConversationNode] = field(default_factory=list)
    edges: List[ConversationEdge] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ConversationSignals:
    step_index: int
    q: float
    TED: float
    continuity: float
    spread: Optional[float] = None
    ted_trusted: Optional[float] = None
    node_count: int = 0
    edge_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "step_index": int(self.step_index),
            "q": round(self.q, 3),
            "TED": round(self.TED, 3),
            "continuity": round(self.continuity, 3),
            "node_count": int(self.node_count),
            "edge_count": int(self.edge_count),
        }
        if self.spread is not None:
            payload["spread"] = round(self.spread, 3)
        if self.ted_trusted is not None:
            payload["ted_trusted"] = round(self.ted_trusted, 3)
        payload.update(self.metadata)
        return payload

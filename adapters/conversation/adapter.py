"""
Main conversation adapter.

Converts dialogue into graph and computes signals.
"""

import numpy as np
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple

from .types import (
    ConversationNode,
    ConversationEdge,
    ConversationTurn,
    ConversationSignals,
)
from collections import deque
from .extractors import SimpleNodeExtractor, SimpleEdgeBuilder, AdvancedNodeExtractor


class ConversationAdapter:
    """
    Adapter that converts conversation streams into graphs.

    Follows same pattern as curriculum adapter:
    - Input: Message stream (role, text)
    - Output: Graph + signals (q, TED, continuity)
    - Compatible with core/signals.py
    """

    def __init__(self, window_size: int = 6):
        # Prefer advanced extractor; fallback to simple
        try:
            self.node_extractor = AdvancedNodeExtractor()
        except Exception:
            self.node_extractor = SimpleNodeExtractor()
        self.edge_builder = SimpleEdgeBuilder()

        # State
        self.turns: List[ConversationTurn] = []
        self.node_registry: Dict[str, ConversationNode] = {}  # id -> node
        self.node_id_counter = 0

        # For mapping to integer IDs (required by core/signals.py)
        self.node_id_to_int: Dict[str, int] = {}
        self.int_to_node_id: Dict[int, str] = {}

        # Sliding window for step-level aggregation
        self.window_size = max(2, int(window_size))
        self._window = deque([], maxlen=self.window_size)
        # For recency features
        self._recent_concepts: deque = deque([], maxlen=self.window_size * 4)

    def process_turn(self, role: str, text: str) -> ConversationSignals:
        """
        Process one conversation turn.

        Args:
            role: "user" or "assistant"
            text: Message text

        Returns:
            ConversationSignals with q, TED, continuity
        """
        turn_index = len(self.turns)

        # Extract nodes
        nodes = self.node_extractor.extract_nodes(text, role, turn_index)

        # Register nodes and assign integer IDs
        for node in nodes:
            if node.id not in self.node_registry:
                self.node_registry[node.id] = node
                # Assign integer ID for core/signals.py compatibility
                int_id = self.node_id_counter
                self.node_id_to_int[node.id] = int_id
                self.int_to_node_id[int_id] = node.id
                self.node_id_counter += 1

        # Build edges
        previous_turn = self.turns[-1] if self.turns else None
        previous_nodes = previous_turn.nodes if previous_turn else []
        previous_text = previous_turn.text if previous_turn else ""

        edges = self.edge_builder.build_edges(
            current_nodes=nodes,
            previous_nodes=previous_nodes,
            current_text=text,
            previous_text=previous_text,
            turn_index=turn_index
        )

        # Create turn
        turn = ConversationTurn(
            turn_index=turn_index,
            role=role,
            text=text,
            nodes=nodes,
            edges=edges
        )
        self.turns.append(turn)

        # Record window
        self._window.append(turn)

        # Compute signals
        signals = self._compute_signals(turn)

        return signals

    def _compute_signals(self, current_turn: ConversationTurn) -> ConversationSignals:
        """
        Compute q, TED, continuity for current turn.

        Following same logic as curriculum adapter.
        """
        turn_index = current_turn.turn_index
        previous_turn = self.turns[turn_index - 1] if turn_index > 0 else None

        # Compute q (quality/coherence)
        q = self._compute_quality(current_turn)

        # Compute TED (drift)
        ted = self._compute_TED(current_turn, previous_turn)

        # Compute continuity (with adjacency-pair boost)
        continuity = self._compute_continuity(current_turn, previous_turn)
        continuity = self._apply_adjacency_boost(continuity, current_turn, previous_turn)

        # Compute spread (topic dispersion)
        spread = self._compute_spread(current_turn)

        # Trusted drift (reliability-weighted)
        ted_trusted = self._compute_trusted_drift(ted, current_turn, previous_turn)

        return ConversationSignals(
            step_index=turn_index,
            q=q,
            TED=ted,
            continuity=continuity,
            spread=spread,
            ted_trusted=ted_trusted,
            node_count=len(current_turn.nodes),
            edge_count=len(current_turn.edges)
        )

    def _compute_quality(self, turn: ConversationTurn) -> float:
        """
        Compute quality = how well-structured is this turn?

        Factors:
        - Edge density (more connections = more coherent)
        - Average edge quality
        - Evidence/claim ratio
        """
        if len(turn.nodes) == 0:
            return 0.5  # Neutral

        # Factor 1: Edge density
        num_nodes = len(turn.nodes)
        max_edges = num_nodes * (num_nodes - 1) / 2
        actual_edges = len([e for e in turn.edges if e.type == "co-mention"])

        if max_edges > 0:
            density = actual_edges / max_edges
        else:
            density = 0.0

        # Factor 2: Average edge quality
        if turn.edges:
            avg_edge_quality = np.mean([e.quality for e in turn.edges])
        else:
            avg_edge_quality = 0.5

        # Factor 3: Balanced node types (concepts + questions = good)
        node_types = [n.type for n in turn.nodes]
        has_concepts = "concept" in node_types
        has_questions = "question" in node_types
        balance_factor = 0.8 if (has_concepts and has_questions) else 0.6

        # Weighted combination
        q = (
            0.3 * density +
            0.4 * avg_edge_quality +
            0.3 * balance_factor
        )

        return np.clip(q, 0, 1)

    def _compute_TED(
        self,
        current_turn: ConversationTurn,
        previous_turn: Optional[ConversationTurn]
    ) -> float:
        """
        Compute TED = drift from previous turn.

        Using Jaccard distance on node sets + embedding distance.
        """
        if previous_turn is None:
            return 0.0  # First turn, no drift

        # Method 1: Node set Jaccard distance
        current_texts = {n.text.lower() for n in current_turn.nodes}
        previous_texts = {n.text.lower() for n in previous_turn.nodes}

        if current_texts or previous_texts:
            intersection = len(current_texts & previous_texts)
            union = len(current_texts | previous_texts)
            jaccard_similarity = intersection / union if union > 0 else 0
            jaccard_distance = 1 - jaccard_similarity
        else:
            jaccard_distance = 0.0

        # Method 2: Embedding centroid distance
        if current_turn.nodes and previous_turn.nodes:
            current_centroid = np.mean(
                [n.embedding for n in current_turn.nodes], axis=0
            )
            previous_centroid = np.mean(
                [n.embedding for n in previous_turn.nodes], axis=0
            )

            # Cosine distance
            dot = np.dot(current_centroid, previous_centroid)
            norm_curr = np.linalg.norm(current_centroid)
            norm_prev = np.linalg.norm(previous_centroid)

            if norm_curr > 0 and norm_prev > 0:
                cosine_sim = dot / (norm_curr * norm_prev)
                cosine_dist = 1 - cosine_sim
            else:
                cosine_dist = 0.0
        else:
            cosine_dist = 0.0

        # Combine both measures
        ted = 0.5 * jaccard_distance + 0.5 * cosine_dist

        return np.clip(ted, 0, 1)

    def _compute_continuity(
        self,
        current_turn: ConversationTurn,
        previous_turn: Optional[ConversationTurn]
    ) -> float:
        """
        Compute continuity = overlap with previous turn.

        High continuity = building on prior concepts.
        """
        if previous_turn is None:
            return 0.0

        if not current_turn.nodes or not previous_turn.nodes:
            return 0.0

        # Method 1: Direct text overlap
        current_texts = {n.text.lower() for n in current_turn.nodes}
        previous_texts = {n.text.lower() for n in previous_turn.nodes}

        intersection = len(current_texts & previous_texts)
        union = len(current_texts | previous_texts)
        text_overlap = intersection / union if union > 0 else 0

        # Method 2: Semantic similarity
        current_centroid = np.mean(
            [n.embedding for n in current_turn.nodes], axis=0
        )
        previous_centroid = np.mean(
            [n.embedding for n in previous_turn.nodes], axis=0
        )

        dot = np.dot(current_centroid, previous_centroid)
        norm_curr = np.linalg.norm(current_centroid)
        norm_prev = np.linalg.norm(previous_centroid)

        if norm_curr > 0 and norm_prev > 0:
            semantic_overlap = dot / (norm_curr * norm_prev)
        else:
            semantic_overlap = 0

        # Combine
        continuity = 0.4 * text_overlap + 0.6 * semantic_overlap

        return np.clip(continuity, 0, 1)

    def _apply_adjacency_boost(
        self,
        base_cont: float,
        current_turn: Optional[ConversationTurn],
        previous_turn: Optional[ConversationTurn],
    ) -> float:
        if not current_turn or not previous_turn:
            return base_cont
        # If previous contained a question and current is opposite role, boost continuity
        prev_has_q = any(n.type == "question" for n in previous_turn.nodes)
        cross_role = (current_turn.nodes and previous_turn.nodes and current_turn.nodes[0].role != previous_turn.nodes[0].role)
        if prev_has_q and cross_role:
            # small bounded boost
            return float(np.clip(base_cont + 0.08, 0, 1))
        return base_cont

    def _compute_spread(self, turn: ConversationTurn) -> float:
        """
        Compute spread = topic dispersion.

        High spread = many disconnected topics.
        Low spread = focused conversation.
        """
        if len(turn.nodes) < 3:
            return 0.0  # Too few nodes to measure dispersion

        # Use simple clustering based on embeddings
        embeddings = np.array([n.embedding for n in turn.nodes])

        # Compute pairwise distances
        num_nodes = len(turn.nodes)
        distances = []
        for i in range(num_nodes):
            for j in range(i + 1, num_nodes):
                dist = 1 - np.dot(embeddings[i], embeddings[j])
                distances.append(dist)

        if distances:
            # High average distance = high spread
            spread = np.mean(distances)
        else:
            spread = 0.0

        return np.clip(spread, 0, 1)

    def _compute_trusted_drift(
        self,
        base_ted: float,
        current_turn: Optional[ConversationTurn],
        previous_turn: Optional[ConversationTurn],
    ) -> float:
        """Weighted drift akin to curriculum trusted drift components.

        Components (α,β,γ,δ configurable via env):
        - Verification (v): fraction of shared concepts across both roles in window
        - Authority (a): role prior (moderator/interviewer > guest > assistant/user equal)
        - Recency (r): reuse of concepts from last W turns
        - Locality (l): node-type weight (concept>question>entity>other)
        Weighted score s = α*v + β*a + γ*r + δ*l; then ted_trusted = base_ted * (1 - s)
        """
        import os
        try:
            alpha = float(os.environ.get("AXIOM_TRUST_ALPHA", 0.4))
            beta  = float(os.environ.get("AXIOM_TRUST_BETA",  0.2))
            gamma = float(os.environ.get("AXIOM_TRUST_GAMMA", 0.2))
            delta = float(os.environ.get("AXIOM_TRUST_DELTA", 0.2))
        except Exception:
            alpha, beta, gamma, delta = 0.4, 0.2, 0.2, 0.2

        if previous_turn is None or current_turn is None:
            return base_ted

        # Verification: shared normalized concept strings this turn vs prev
        curr_concepts = {n.text.lower() for n in current_turn.nodes if n.type in {"concept","entity"}}
        prev_concepts = {n.text.lower() for n in previous_turn.nodes if n.type in {"concept","entity"}}
        union = len(curr_concepts | prev_concepts)
        v = (len(curr_concepts & prev_concepts) / union) if union > 0 else 0.0

        # Authority: simple role prior (if roles alternate and one is interviewer/moderator in metadata)
        def _role_weight(nodes: List[ConversationNode]) -> float:
            if not nodes:
                return 0.5
            role = nodes[0].role.lower()
            # Conversation roles vary; keep neutral with slight boost for assistant as "expert" analog
            return 0.55 if role == "assistant" else 0.5
        a = (_role_weight(previous_turn.nodes) + _role_weight(current_turn.nodes)) / 2.0

        # Recency: fraction of current concepts seen in recent history
        seen = 0
        for c in curr_concepts:
            if c in self._recent_concepts:
                seen += 1
        r = (seen / max(1, len(curr_concepts))) if curr_concepts else 0.0

        # Locality: weight by node type presence (concept heavy → higher locality)
        types = [n.type for n in current_turn.nodes]
        l = 0.0
        if types:
            l = (
                1.0 * (types.count("concept") / len(types)) +
                0.8 * (types.count("question") / len(types)) +
                0.6 * (types.count("entity") / len(types))
            )

        score = float(np.clip(alpha * v + beta * a + gamma * r + delta * l, 0, 1))
        ted_trusted = float(np.clip(base_ted * (1.0 - score), 0, 1))

        # Update recency buffer
        for c in curr_concepts:
            self._recent_concepts.append(c)

        return ted_trusted

    def get_recent_signals(self, window_size: int = 5) -> List[ConversationSignals]:
        """Get signals for recent turns."""
        signals = []
        start_idx = max(0, len(self.turns) - window_size)

        for turn in self.turns[start_idx:]:
            # Recompute signals for each turn
            previous_turn = self.turns[turn.turn_index - 1] if turn.turn_index > 0 else None
            ted = self._compute_TED(turn, previous_turn)
            cont = self._apply_adjacency_boost(
                self._compute_continuity(turn, previous_turn),
                turn,
                previous_turn,
            )
            sig = ConversationSignals(
                step_index=turn.turn_index,
                q=self._compute_quality(turn),
                TED=ted,
                continuity=cont,
                spread=self._compute_spread(turn),
                ted_trusted=self._compute_trusted_drift(ted, turn, previous_turn),
                node_count=len(turn.nodes),
                edge_count=len(turn.edges)
            )
            signals.append(sig)

        return signals

    def get_conversation_summary(self) -> Dict:
        """Get overall conversation statistics."""
        if not self.turns:
            return {
                "total_turns": 0,
                "total_nodes": 0,
                "total_edges": 0,
                "avg_q": 0,
                "avg_TED": 0,
                "avg_continuity": 0
            }

        signals = self.get_recent_signals(len(self.turns))

        return {
            "total_turns": len(self.turns),
            "total_nodes": len(self.node_registry),
            "total_edges": sum(len(t.edges) for t in self.turns),
            "avg_q": round(np.mean([s.q for s in signals]), 3),
            "avg_TED": round(np.mean([s.TED for s in signals if s.TED is not None]), 3),
            "avg_continuity": round(np.mean([s.continuity for s in signals]), 3),
            "node_types": self._count_node_types(),
            "edge_types": self._count_edge_types()
        }

    def _count_node_types(self) -> Dict[str, int]:
        """Count nodes by type."""
        counts = defaultdict(int)
        for node in self.node_registry.values():
            counts[node.type] += 1
        return dict(counts)

    def _count_edge_types(self) -> Dict[str, int]:
        """Count edges by type."""
        counts = defaultdict(int)
        for turn in self.turns:
            for edge in turn.edges:
                counts[edge.type] += 1
        return dict(counts)

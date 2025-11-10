from __future__ import annotations

import re
import uuid
from typing import Dict, Iterable, List

from adapters.conversation.types import ConversationEdge, ConversationNode


_QUESTION_WORDS = {"who", "what", "when", "where", "why", "how", "is", "are", "do", "does", "did", "can", "could"}


class BaseNodeExtractor:
    SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
    QUESTION_RE = re.compile(r"\?$")

    def extract_nodes(self, text: str, role: str, turn_index: int) -> List[ConversationNode]:
        raise NotImplementedError

    def _clean_text(self, text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    def _create_node(
        self,
        text: str,
        node_type: str,
        role: str,
        turn_index: int,
        metadata: Dict[str, object] | None = None,
    ) -> ConversationNode:
        metadata = dict(metadata or {})
        node_id = metadata.get("id")
        if not node_id:
            node_id = f"{turn_index}_{uuid.uuid4().hex[:8]}"
        return ConversationNode(
            id=str(node_id),
            text=text,
            type=node_type,
            role=role,
            turn_index=turn_index,
            metadata=metadata,
        )


class SimpleNodeExtractor(BaseNodeExtractor):
    def extract_nodes(self, text: str, role: str, turn_index: int) -> List[ConversationNode]:
        clean = self._clean_text(text)
        if not clean:
            return []
        return [self._create_node(clean, "concept", role, turn_index)]


class AdvancedNodeExtractor(SimpleNodeExtractor):
    def extract_nodes(self, text: str, role: str, turn_index: int) -> List[ConversationNode]:
        clean = self._clean_text(text)
        if not clean:
            return []
        sentences = [s.strip() for s in self.SENTENCE_SPLIT_RE.split(clean) if s.strip()]
        if len(sentences) <= 1:
            return [self._create_node(clean, self._classify(clean, role), role, turn_index, metadata={"segment": 0})]
        nodes = []
        for idx, sentence in enumerate(sentences):
            node_text = self._clean_text(sentence)
            if not node_text:
                continue
            node_type = self._classify(node_text, role)
            nodes.append(self._create_node(node_text, node_type, role, turn_index, metadata={"segment": idx}))
        return nodes

    def _classify(self, text: str, role: str) -> str:
        if self.QUESTION_RE.search(text) or text.split(" ", 1)[0].lower() in _QUESTION_WORDS:
            return "question"
        if role == "assistant":
            return "answer"
        return "concept"

class SimpleEdgeBuilder:
    def build_edges(
        self,
        current_nodes: Iterable[ConversationNode],
        previous_nodes: Iterable[ConversationNode],
        current_text: str,
        previous_text: str,
        turn_index: int,
    ) -> List[ConversationEdge]:
        edges: List[ConversationEdge] = []
        prev_list = list(previous_nodes)
        curr_list = list(current_nodes)
        if not prev_list or not curr_list:
            return edges
        edge_type = "reply" if turn_index > 0 else "adjacency"
        for prev in prev_list:
            for curr in curr_list:
                edges.append(
                    ConversationEdge(
                        source=prev.id,
                        target=curr.id,
                        type=edge_type,
                        weight=1.0,
                        quality=1.0,
                    )
                )
        return edges

    def _classify(self, text: str, role: str) -> str:
        if self.QUESTION_RE.search(text) or text.split(" ", 1)[0].lower() in _QUESTION_WORDS:
            return "question"
        if role == "assistant":
            return "answer"
        return "concept"

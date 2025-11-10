"""
Conversation adapter for AxiomicAgent.

Converts dialogue streams into graphs for metacognitive analysis.
"""

from .adapter import ConversationAdapter
from .types import ConversationNode, ConversationEdge, ConversationTurn

__all__ = ["ConversationAdapter", "ConversationNode", "ConversationEdge", "ConversationTurn"]

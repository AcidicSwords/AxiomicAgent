"""
Node and edge extraction from conversation text.

Upgraded pipeline:
- AdvancedNodeExtractor uses spaCy for noun-chunks/NER and
  sentence-transformers for robust semantic embeddings when available.
- Falls back to SimpleNodeExtractor if dependencies are missing.
"""

import re
import hashlib
from typing import List, Set, Tuple, Optional
import numpy as np
from collections import defaultdict

from .types import ConversationNode, ConversationEdge

# Optional heavy deps
_HAVE_SPACY = False
_HAVE_ST = False
try:
    import spacy  # type: ignore
    _HAVE_SPACY = True
except Exception:
    spacy = None  # type: ignore
try:
    from sentence_transformers import SentenceTransformer  # type: ignore
    _HAVE_ST = True
except Exception:
    SentenceTransformer = None  # type: ignore


class SimpleNodeExtractor:
    """
    Lightweight node extractor using pattern matching.

    For production: replace with spaCy + sentence-transformers.
    For MVP: use regex patterns and simple heuristics.
    """

    def __init__(self):
        # Patterns for different node types
        self.stopwords = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
            "have", "has", "had", "do", "does", "did", "will", "would", "should",
            "could", "may", "might", "can", "this", "that", "these", "those",
            "it", "its", "they", "them", "their", "i", "you", "we", "he", "she"
        }

    def extract_nodes(
        self, text: str, role: str, turn_index: int
    ) -> List[ConversationNode]:
        """
        Extract nodes from text.

        Returns list of ConversationNode objects.
        """
        nodes = []

        # 1. Extract key noun phrases (concepts)
        concepts = self._extract_concepts(text)
        for concept in concepts:
            nodes.append(self._create_node(
                text=concept,
                node_type="concept",
                role=role,
                turn_index=turn_index
            ))

        # 2. Extract questions
        questions = self._extract_questions(text)
        for question in questions:
            nodes.append(self._create_node(
                text=question,
                node_type="question",
                role=role,
                turn_index=turn_index
            ))

        # 3. Extract technical terms
        tech_terms = self._extract_technical_terms(text)
        for term in tech_terms:
            nodes.append(self._create_node(
                text=term,
                node_type="entity",
                role=role,
                turn_index=turn_index,
                metadata={"entity_type": "TECH"}
            ))

        return nodes

    def _extract_concepts(self, text: str) -> Set[str]:
        """Extract key concepts from text."""
        concepts = set()

        # Title-case phrases (e.g., "Claude Code", "Axiomic Agent")
        title_case = re.findall(
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',
            text
        )
        concepts.update(title_case)

        # Multi-word technical phrases
        # Pattern: lowercase word + capitalized word
        tech_phrases = re.findall(
            r'\b[a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',
            text
        )
        concepts.update(tech_phrases)

        # Filter stopwords and short phrases
        concepts = {
            c for c in concepts
            if len(c) > 3 and c.lower() not in self.stopwords
        }

        return concepts

    def _extract_questions(self, text: str) -> List[str]:
        """Extract questions from text."""
        # Split into sentences and find questions
        sentences = re.split(r'[.!?]+', text)
        questions = [
            s.strip() for s in sentences
            if s.strip().endswith('?') or
            any(s.strip().lower().startswith(q) for q in ['what', 'how', 'why', 'when', 'where', 'who', 'can', 'do', 'does', 'is', 'are'])
        ]
        return questions[:3]  # Limit to top 3

    def _extract_technical_terms(self, text: str) -> Set[str]:
        """Extract technical terms (camelCase, snake_case, ACRONYMS)."""
        terms = set()

        # camelCase
        camel = re.findall(r'\b[a-z]+[A-Z]\w+\b', text)
        terms.update(camel)

        # snake_case
        snake = re.findall(r'\b[a-z]+_[a-z_]+\b', text)
        terms.update(snake)

        # ACRONYMS (3+ caps)
        acronyms = re.findall(r'\b[A-Z]{3,}\b', text)
        terms.update(acronyms)

        # Programming terms
        code_terms = re.findall(r'`([^`]+)`', text)
        terms.update(code_terms)

        return terms

    def _create_node(
        self,
        text: str,
        node_type: str,
        role: str,
        turn_index: int,
        metadata: dict = None
    ) -> ConversationNode:
        """Create a ConversationNode."""
        # Generate deterministic ID
        node_id = self._generate_node_id(text, node_type, turn_index)

        # Simple embedding: TF-IDF-like vector
        embedding = self._simple_embedding(text)

        return ConversationNode(
            id=node_id,
            text=text,
            type=node_type,
            role=role,
            embedding=embedding,
            turn_index=turn_index,
            metadata=metadata or {}
        )

    def _generate_node_id(self, text: str, node_type: str, turn_index: int) -> str:
        """Generate unique but deterministic node ID."""
        content = f"{node_type}:{text.lower()}:{turn_index}"
        hash_obj = hashlib.md5(content.encode())
        return f"{node_type[:3]}_{hash_obj.hexdigest()[:12]}"

    def _simple_embedding(self, text: str) -> np.ndarray:
        """
        Simple embedding based on character/word features.

        For production: replace with sentence-transformers.
        """
        # Normalized word count
        words = text.lower().split()
        word_count = len(words)

        # Character features
        char_features = [
            len(text) / 100.0,  # Length (normalized)
            text.count(' ') / max(len(text), 1),  # Space ratio
            sum(c.isupper() for c in text) / max(len(text), 1),  # Cap ratio
            sum(c.isdigit() for c in text) / max(len(text), 1),  # Digit ratio
        ]

        # Simple word hash features (for semantic similarity proxy)
        word_hashes = [hash(w) % 1000 / 1000.0 for w in words[:10]]
        word_hashes += [0.5] * (10 - len(word_hashes))  # Pad to 10

        embedding = np.array(char_features + word_hashes, dtype=np.float32)
        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding


class SimpleEdgeBuilder:
    """
    Build edges between nodes based on text relationships.
    """

    def build_edges(
        self,
        current_nodes: List[ConversationNode],
        previous_nodes: List[ConversationNode],
        current_text: str,
        previous_text: str,
        turn_index: int
    ) -> List[ConversationEdge]:
        """
        Build edges within and across turns.
        """
        edges = []

        # 1. Within-turn edges (co-mention)
        edges.extend(self._build_comention_edges(current_nodes, turn_index))

        # 2. Cross-turn edges (reply structure)
        if previous_nodes:
            edges.extend(self._build_reply_edges(
                current_nodes, previous_nodes, turn_index
            ))

        return edges

    def _build_comention_edges(
        self, nodes: List[ConversationNode], turn_index: int
    ) -> List[ConversationEdge]:
        """Build co-mention edges within a turn."""
        edges = []

        for i, node_a in enumerate(nodes):
            for node_b in nodes[i+1:]:
                # Compute similarity
                sim = self._cosine_similarity(
                    node_a.embedding, node_b.embedding
                )

                # Only connect if sufficiently similar
                if sim > 0.3:
                    edge = ConversationEdge(
                        source=node_a.id,
                        target=node_b.id,
                        type="co-mention",
                        weight=sim,
                        quality=sim,  # Quality = similarity for co-mention
                        turn_index=turn_index
                    )
                    edges.append(edge)

        return edges

    def _build_reply_edges(
        self,
        current_nodes: List[ConversationNode],
        previous_nodes: List[ConversationNode],
        turn_index: int
    ) -> List[ConversationEdge]:
        """Build reply edges from previous turn to current turn."""
        edges = []

        # Only connect across roles (user -> assistant or vice versa)
        if not current_nodes or not previous_nodes:
            return edges

        curr_role = current_nodes[0].role
        prev_role = previous_nodes[0].role

        if curr_role == prev_role:
            return edges  # Don't connect same-role turns

        for prev_node in previous_nodes:
            for curr_node in current_nodes:
                # Compute semantic similarity
                sim = self._cosine_similarity(
                    prev_node.embedding, curr_node.embedding
                )

                # Also check lexical overlap
                lexical = self._lexical_overlap(prev_node.text, curr_node.text)

                # Connect if either metric is high
                if sim > 0.4 or lexical > 0.3:
                    # Quality based on both factors
                    quality = 0.6 * sim + 0.4 * lexical

                    edge = ConversationEdge(
                        source=prev_node.id,
                        target=curr_node.id,
                        type="reply",
                        weight=max(sim, lexical),
                        quality=quality,
                        turn_index=turn_index
                    )
                    edges.append(edge)

        return edges

    def _cosine_similarity(self, emb_a: np.ndarray, emb_b: np.ndarray) -> float:
        """Compute cosine similarity between embeddings."""
        dot_product = np.dot(emb_a, emb_b)
        norm_a = np.linalg.norm(emb_a)
        norm_b = np.linalg.norm(emb_b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return float(np.clip(dot_product / (norm_a * norm_b), 0, 1))

    def _lexical_overlap(self, text_a: str, text_b: str) -> float:
        """Compute Jaccard similarity of word sets."""
        words_a = set(text_a.lower().split())
        words_b = set(text_b.lower().split())

        if not words_a or not words_b:
            return 0.0

        intersection = len(words_a & words_b)
        union = len(words_a | words_b)

        return intersection / union if union > 0 else 0.0


class AdvancedNodeExtractor(SimpleNodeExtractor):
    """
    High-quality extractor leveraging spaCy + sentence-transformers when available.
    Falls back gracefully to SimpleNodeExtractor components.
    """

    def __init__(self):
        super().__init__()
        self._nlp = None
        self._st_model = None
        if _HAVE_SPACY:
            try:
                # Try to load a small English model; fallback to blank if not installed
                try:
                    self._nlp = spacy.load("en_core_web_sm")
                except Exception:
                    self._nlp = spacy.blank("en")
                    if "sentencizer" not in self._nlp.pipe_names:
                        self._nlp.add_pipe("sentencizer")
            except Exception:
                self._nlp = None
        if _HAVE_ST:
            try:
                self._st_model = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception:
                self._st_model = None

    def extract_nodes(self, text: str, role: str, turn_index: int) -> List[ConversationNode]:
        if not self._nlp:
            # Fallback to simple behavior entirely
            return super().extract_nodes(text, role, turn_index)

        doc = self._nlp(text)
        nodes: List[ConversationNode] = []

        # 1) Noun chunks as candidate concepts
        concepts: Set[str] = set()
        for chunk in getattr(doc, "noun_chunks", []):
            phrase = chunk.text.strip()
            if len(phrase) < 4:
                continue
            # Filter trivial stopwords-only phrases
            toks = [t.lemma_.lower() for t in chunk if not t.is_stop and t.is_alpha]
            if not toks:
                continue
            norm = " ".join(toks)
            if len(norm) < 3:
                continue
            concepts.add(norm)

        # 2) Named entities as entities
        entities: Set[str] = set()
        if getattr(doc, "ents", None):
            for ent in doc.ents:
                label = ent.label_.upper()
                txt = ent.text.strip()
                if len(txt) >= 3:
                    entities.add(f"{txt}")

        # 3) Questions (sentences ending with ?)
        questions: List[str] = []
        for sent in doc.sents:
            stxt = sent.text.strip()
            if stxt.endswith("?"):
                questions.append(stxt)

        # Create nodes with robust embeddings
        for concept in list(concepts)[:8]:
            nodes.append(self._create_node(concept, "concept", role, turn_index))
        for ent in list(entities)[:6]:
            nodes.append(self._create_node(ent, "entity", role, turn_index, {"ner": True}))
        for q in questions[:3]:
            nodes.append(self._create_node(q, "question", role, turn_index))

        return nodes

    def _create_node(
        self,
        text: str,
        node_type: str,
        role: str,
        turn_index: int,
        metadata: Optional[dict] = None,
    ) -> ConversationNode:
        node = super()._create_node(text, node_type, role, turn_index, metadata or {})
        if self._st_model is not None:
            try:
                vec = self._st_model.encode([text], normalize_embeddings=True)[0]
                node.embedding = np.array(vec, dtype=np.float32)
            except Exception:
                pass
        return node

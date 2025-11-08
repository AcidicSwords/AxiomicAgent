# Conversation Adapter: Claude-Grounded Implementation
## Bridging Communication Theory and LLM Reality

**Version:** 1.0
**Date:** 2025-01-07
**Purpose:** Practical conversation adapter design grounded in actual Claude API behavior

---

## Executive Summary

The v3 design spec is theoretically sound but needs grounding in **what's actually measurable and steerable** in Claude API conversations. This document bridges that gap by analyzing:

1. What signals Claude *actually* exposes
2. What graph structures are *actually* computable from text
3. What interventions *actually* affect Claude behavior
4. What regime detection is *actually* feasible

**Core Insight:** We can't directly measure Claude's internal state, but we can **infer graph dynamics from observable text patterns** that correlate with internal processing states.

---

## I. What Claude Actually Exposes

### A. Available Signals (API Level)

```python
# What we CAN measure from Claude API:
observable_signals = {
    # Response level:
    "text_output": "Full response text",
    "token_count": "Via tiktoken or API metadata",
    "stop_reason": "end_turn, max_tokens, stop_sequence",

    # Conversation level:
    "message_history": "All prior turns",
    "system_prompt": "Initial instructions",

    # NOT available:
    "attention_weights": False,  # ❌
    "hidden_states": False,      # ❌
    "token_probabilities": False, # ❌ (no logprobs in API)
    "internal_reasoning": False,  # ❌ (extended thinking not returned)
}
```

**Implication:** Our graph must be built from **text-level features**, not internal model states.

### B. Inferable Signals (Text Analysis)

```python
# What we CAN infer from text:
inferable_signals = {
    # Lexical:
    "vocabulary_diversity": "Type-token ratio, lexical density",
    "term_repetition": "N-gram overlap between turns",
    "concept_mentions": "Named entities, key phrases",

    # Syntactic:
    "sentence_complexity": "Parse tree depth, clause count",
    "question_density": "Questions per 100 tokens",
    "hedge_words": "might, could, perhaps, possibly",

    # Semantic:
    "topic_shift": "Embedding cosine distance",
    "claim_structure": "Assertion + evidence patterns",
    "reference_density": "Backward references to prior turns",

    # Pragmatic:
    "speech_act_type": "Question, assertion, acknowledgment",
    "epistemic_stance": "Certainty markers vs hedges",
    "turn_coherence": "Semantic similarity to user message",
}
```

**These become our node and edge features.**

---

## II. Graph Construction from Observable Text

### A. Node Extraction Strategy

**Problem:** The v3 spec calls for nodes = "claims, evidence, emotions, topics, constraints." How do we extract these reliably?

**Claude-Grounded Approach:**

```python
class ConversationNodeExtractor:
    """Extract graph nodes from Claude conversation text"""

    def __init__(self):
        self.nlp = spacy.load("en_core_web_trf")  # Transformer-based
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

    def extract_nodes(self, message_text, role):
        """
        Extract nodes from a single message
        Returns: List[Node]
        """
        doc = self.nlp(message_text)
        nodes = []

        # 1. Extract key noun phrases (concepts)
        for chunk in doc.noun_chunks:
            if self.is_significant_concept(chunk):
                nodes.append({
                    "type": "concept",
                    "text": chunk.text,
                    "embedding": self.embedder.encode(chunk.text),
                    "role": role,  # user or assistant
                })

        # 2. Extract claims (sentences with assertion structure)
        for sent in doc.sents:
            if self.is_claim(sent):
                nodes.append({
                    "type": "claim",
                    "text": sent.text,
                    "embedding": self.embedder.encode(sent.text),
                    "role": role,
                    "confidence": self.measure_certainty(sent),
                })

        # 3. Extract questions (exploration nodes)
        for sent in doc.sents:
            if sent.text.strip().endswith("?"):
                nodes.append({
                    "type": "question",
                    "text": sent.text,
                    "embedding": self.embedder.encode(sent.text),
                    "role": role,
                })

        # 4. Extract entities (grounding nodes)
        for ent in doc.ents:
            if ent.label_ in ["PERSON", "ORG", "GPE", "PRODUCT", "EVENT"]:
                nodes.append({
                    "type": "entity",
                    "text": ent.text,
                    "label": ent.label_,
                    "embedding": self.embedder.encode(ent.text),
                    "role": role,
                })

        return nodes

    def is_significant_concept(self, chunk):
        """Filter out trivial noun phrases"""
        # Must be at least 2 tokens, not all stopwords
        if len(chunk) < 2:
            return False
        if all(token.is_stop for token in chunk):
            return False
        return True

    def is_claim(self, sent):
        """Detect if sentence makes an assertion"""
        # Has subject + verb + object/complement
        has_subject = any(token.dep_ == "nsubj" for token in sent)
        has_verb = any(token.pos_ == "VERB" for token in sent)
        is_question = sent.text.strip().endswith("?")

        return has_subject and has_verb and not is_question

    def measure_certainty(self, sent):
        """Measure epistemic certainty of claim"""
        hedge_words = {"might", "could", "possibly", "perhaps", "maybe"}
        certainty_words = {"definitely", "certainly", "clearly", "obviously"}

        tokens_lower = {t.text.lower() for t in sent}

        if tokens_lower & hedge_words:
            return 0.5  # Hedged claim
        elif tokens_lower & certainty_words:
            return 0.95  # Confident claim
        else:
            return 0.75  # Default assertion
```

**Key Insight:** We can't parse Claude's "internal claims" but we can parse **textual claim structures** that correlate with confident vs exploratory responses.

### B. Edge Construction Strategy

**Problem:** Edges need semantic meaning (support, refute, elaborate, etc.)

**Claude-Grounded Approach:**

```python
class ConversationEdgeBuilder:
    """Build edges between nodes based on text relationships"""

    def build_edges(self, nodes_current_turn, nodes_previous_turn,
                    current_text, previous_text):
        """
        Build edges within and across turns
        Returns: List[Edge]
        """
        edges = []

        # 1. Within-turn edges (co-mention)
        edges.extend(self.build_comention_edges(nodes_current_turn))

        # 2. Cross-turn edges (reply structure)
        edges.extend(self.build_reply_edges(
            nodes_current_turn, nodes_previous_turn,
            current_text, previous_text
        ))

        # 3. Argument structure edges (claim ← evidence)
        edges.extend(self.build_argument_edges(nodes_current_turn, current_text))

        return edges

    def build_comention_edges(self, nodes):
        """Nodes mentioned in same turn are co-mentioned"""
        edges = []
        for i, node_a in enumerate(nodes):
            for node_b in nodes[i+1:]:
                # Semantic similarity above threshold
                sim = cosine_similarity(
                    node_a["embedding"], node_b["embedding"]
                )
                if sim > 0.3:  # Related concepts
                    edges.append({
                        "source": node_a["id"],
                        "target": node_b["id"],
                        "type": "co-mention",
                        "weight": sim,
                        "quality": sim,  # Higher similarity = higher quality
                    })
        return edges

    def build_reply_edges(self, current_nodes, prev_nodes,
                         current_text, prev_text):
        """Build edges from user concepts → assistant concepts"""
        edges = []

        for user_node in prev_nodes:
            if user_node["role"] != "user":
                continue

            for assist_node in current_nodes:
                if assist_node["role"] != "assistant":
                    continue

                # Check if assistant node addresses user node
                sim = cosine_similarity(
                    user_node["embedding"], assist_node["embedding"]
                )

                # Also check textual continuity (lexical overlap)
                lexical_overlap = self.compute_lexical_overlap(
                    user_node["text"], assist_node["text"]
                )

                if sim > 0.4 or lexical_overlap > 0.3:
                    edges.append({
                        "source": user_node["id"],
                        "target": assist_node["id"],
                        "type": "reply",
                        "weight": max(sim, lexical_overlap),
                        "quality": self.assess_reply_quality(
                            user_node, assist_node, current_text
                        ),
                    })

        return edges

    def build_argument_edges(self, nodes, text):
        """Detect claim-evidence structure"""
        edges = []

        claims = [n for n in nodes if n["type"] == "claim"]
        potential_evidence = [n for n in nodes if n["type"] in ["concept", "entity"]]

        for claim in claims:
            for evidence in potential_evidence:
                # Check if evidence appears before claim in text
                if text.find(evidence["text"]) < text.find(claim["text"]):
                    # Evidence precedes claim → potential support
                    sim = cosine_similarity(
                        claim["embedding"], evidence["embedding"]
                    )
                    if sim > 0.5:
                        edges.append({
                            "source": evidence["id"],
                            "target": claim["id"],
                            "type": "support",
                            "weight": sim,
                            "quality": sim,
                        })

        return edges

    def assess_reply_quality(self, user_node, assist_node, response_text):
        """
        How well does assistant address user node?
        Claude-specific heuristics
        """
        quality_factors = {}

        # 1. Direct acknowledgment (high quality)
        acknowledgment_patterns = [
            "you're asking about", "regarding", "as for",
            "to answer your question", "you mentioned"
        ]
        has_acknowledgment = any(
            p in response_text.lower()
            for p in acknowledgment_patterns
        )
        quality_factors["acknowledgment"] = 1.0 if has_acknowledgment else 0.5

        # 2. Elaboration (medium-high quality)
        response_length = len(response_text.split())
        quality_factors["elaboration"] = min(1.0, response_length / 100)

        # 3. Semantic alignment
        quality_factors["semantic"] = cosine_similarity(
            user_node["embedding"], assist_node["embedding"]
        )

        # Weighted combination
        quality = (
            0.3 * quality_factors["acknowledgment"] +
            0.3 * quality_factors["semantic"] +
            0.4 * quality_factors["elaboration"]
        )

        return quality

    def compute_lexical_overlap(self, text_a, text_b):
        """Jaccard similarity of word sets"""
        words_a = set(text_a.lower().split())
        words_b = set(text_b.lower().split())

        if not words_a or not words_b:
            return 0.0

        return len(words_a & words_b) / len(words_a | words_b)
```

---

## III. Metric Computation: What's Actually Measurable

### A. Quality (q) - Coherence

**Theoretical Definition:** Local coherence; claim–reason–warrant density

**Practical Measurement:**

```python
def compute_q_practical(graph, turn_nodes):
    """
    Measure quality = how well-structured is this turn's subgraph
    """
    if len(turn_nodes) == 0:
        return 0.5  # Neutral

    # Extract subgraph for this turn
    subgraph = graph.subgraph([n["id"] for n in turn_nodes])

    # Factor 1: Edge density (more connections = more coherent)
    max_edges = len(turn_nodes) * (len(turn_nodes) - 1) / 2
    actual_edges = subgraph.number_of_edges()
    density = actual_edges / max_edges if max_edges > 0 else 0

    # Factor 2: Average edge quality
    if actual_edges > 0:
        avg_edge_quality = np.mean([
            graph.edges[e]["quality"] for e in subgraph.edges()
        ])
    else:
        avg_edge_quality = 0

    # Factor 3: Claim-evidence ratio (good arguments have support)
    claims = [n for n in turn_nodes if n["type"] == "claim"]
    evidence = [n for n in turn_nodes if n["type"] in ["concept", "entity"]]

    if len(claims) > 0:
        support_ratio = len(evidence) / len(claims)
        support_factor = min(1.0, support_ratio / 2)  # Ideal: 2 evidence per claim
    else:
        support_factor = 0.5

    # Weighted combination
    q = (
        0.3 * density +
        0.4 * avg_edge_quality +
        0.3 * support_factor
    )

    return clip(q, 0, 1)
```

**What this captures in Claude:**
- High q = Claude's response is internally coherent (concepts connect)
- Low q = Claude's response is scattered or listing unrelated points

### B. TED (Topic/Concept Drift)

**Theoretical Definition:** Graph change per step

**Practical Measurement:**

```python
def compute_TED_practical(graph_t, graph_t_minus_1):
    """
    Measure drift = how much did the conversation shift?
    """
    if graph_t_minus_1 is None:
        return 0.0  # First turn, no drift

    # Method 1: Node set Jaccard distance
    nodes_t = set(graph_t.nodes())
    nodes_prev = set(graph_t_minus_1.nodes())

    jaccard = len(nodes_t & nodes_prev) / len(nodes_t | nodes_prev) if (nodes_t | nodes_prev) else 0
    jaccard_distance = 1 - jaccard

    # Method 2: Embedding centroid distance
    if len(nodes_t) > 0 and len(nodes_prev) > 0:
        centroid_t = np.mean([
            graph_t.nodes[n]["embedding"] for n in nodes_t
        ], axis=0)
        centroid_prev = np.mean([
            graph_t_minus_1.nodes[n]["embedding"] for n in nodes_prev
        ], axis=0)

        cosine_dist = 1 - cosine_similarity(centroid_t, centroid_prev)
    else:
        cosine_dist = 0

    # Combine both measures
    TED = 0.5 * jaccard_distance + 0.5 * cosine_dist

    return clip(TED, 0, 1)
```

**What this captures in Claude:**
- High TED = Claude shifted topics significantly (new concepts introduced)
- Low TED = Claude staying on same topic (repeating prior concepts)

### C. Continuity

**Theoretical Definition:** Overlap with prior phase's active nodes

**Practical Measurement:**

```python
def compute_continuity_practical(turn_t_nodes, turn_t_minus_1_nodes):
    """
    Measure continuity = how much carryover from previous turn?
    """
    if not turn_t_minus_1_nodes:
        return 0.0

    # Method 1: Direct node overlap (by text)
    texts_t = {n["text"].lower() for n in turn_t_nodes}
    texts_prev = {n["text"].lower() for n in turn_t_minus_1_nodes}

    overlap = len(texts_t & texts_prev) / len(texts_t | texts_prev) if (texts_t | texts_prev) else 0

    # Method 2: Semantic similarity of node sets
    if turn_t_nodes and turn_t_minus_1_nodes:
        emb_t = np.mean([n["embedding"] for n in turn_t_nodes], axis=0)
        emb_prev = np.mean([n["embedding"] for n in turn_t_minus_1_nodes], axis=0)

        semantic_overlap = cosine_similarity(emb_t, emb_prev)
    else:
        semantic_overlap = 0

    # Combine
    continuity = 0.4 * overlap + 0.6 * semantic_overlap

    return clip(continuity, 0, 1)
```

**What this captures in Claude:**
- High continuity = Claude building on user's concepts (active listening)
- Low continuity = Claude introducing new frame (exploration or drift)

### D. Spread (Topic Dispersion)

**Theoretical Definition:** Topical dispersion / entropy

**Practical Measurement:**

```python
def compute_spread_practical(turn_nodes, graph):
    """
    Measure spread = how scattered are topics?
    """
    if len(turn_nodes) < 3:
        return 0.0  # Too few nodes to measure spread

    # Cluster nodes by semantic similarity
    embeddings = np.array([n["embedding"] for n in turn_nodes])

    # Use simple k-means clustering (k=3 for small graphs)
    from sklearn.cluster import KMeans
    k = min(3, len(turn_nodes))
    kmeans = KMeans(n_clusters=k, random_state=42)
    labels = kmeans.fit_predict(embeddings)

    # Compute entropy of cluster distribution
    cluster_counts = np.bincount(labels)
    cluster_probs = cluster_counts / len(turn_nodes)

    entropy = -np.sum(cluster_probs * np.log(cluster_probs + 1e-10))
    max_entropy = np.log(k)

    spread = entropy / max_entropy if max_entropy > 0 else 0

    return spread
```

**What this captures in Claude:**
- High spread = Claude covering many disconnected topics
- Low spread = Claude focused on single coherent topic

---

## IV. Regime Detection: Feasible Patterns

### A. Detectable Regimes from Text

Based on observable signals, we can detect:

| Regime | Observable Signature | Detection Logic |
|--------|---------------------|-----------------|
| **Stuck (Low TED)** | q high, TED < 0.15, continuity > 0.7 | Repetitive language, high lexical overlap |
| **Exploring (Healthy)** | q medium, 0.2 < TED < 0.4, continuity 0.3-0.6 | New concepts + references to prior |
| **Scattered** | q < 0.5, TED > 0.5, spread > 0.6 | Low edge density, many clusters |
| **Deep Dive** | q > 0.75, TED 0.1-0.2, continuity > 0.6 | High coherence, gradual deepening |
| **Pivot** | TED > 0.5, continuity 0.2-0.4 | Sudden topic shift with some bridge concepts |

**Implementation:**

```python
class RegimeClassifier:
    """Classify conversation regime from metrics"""

    def classify(self, signals):
        q = signals["q"]
        ted = signals["TED"]
        cont = signals["continuity"]
        spread = signals["spread"]

        # Stuck: Premature convergence
        if q > 0.80 and ted < 0.15 and cont > 0.65:
            return {
                "regime": "stuck",
                "confidence": 0.9,
                "warning": "Premature convergence detected"
            }

        # Scattered: Too chaotic
        if q < 0.50 and ted > 0.45 and spread > 0.6:
            return {
                "regime": "scattered",
                "confidence": 0.85,
                "warning": "Conversation fragmented"
            }

        # Exploring: Healthy
        if 0.55 < q < 0.85 and 0.20 < ted < 0.40 and 0.3 < cont < 0.6:
            return {
                "regime": "exploring",
                "confidence": 0.8,
                "status": "Optimal learning zone"
            }

        # Deep dive: Focused investigation
        if q > 0.75 and 0.10 < ted < 0.25 and cont > 0.55 and spread < 0.3:
            return {
                "regime": "deep_dive",
                "confidence": 0.75,
                "status": "Sustained focus"
            }

        # Pivot: Major transition
        if ted > 0.50 and 0.2 < cont < 0.5:
            return {
                "regime": "pivot",
                "confidence": 0.7,
                "status": "Topic transition detected"
            }

        # Default
        return {
            "regime": "mixed",
            "confidence": 0.5,
            "status": "No clear pattern"
        }
```

### B. Claude-Specific Behavioral Signatures

**What we can detect about Claude's behavior:**

```python
class ClaudeBehaviorAnalyzer:
    """Detect Claude-specific patterns"""

    def analyze_claude_response(self, response_text, context):
        """Analyze Claude's response characteristics"""

        patterns = {}

        # 1. Hedge density (epistemic uncertainty)
        hedge_words = ["might", "could", "possibly", "perhaps", "seems", "likely"]
        word_count = len(response_text.split())
        hedge_count = sum(response_text.lower().count(h) for h in hedge_words)
        patterns["hedge_density"] = hedge_count / word_count if word_count > 0 else 0

        # 2. Acknowledgment patterns (active listening)
        ack_patterns = [
            "you mentioned", "you asked", "you're right", "i see",
            "that's a good point", "as you noted"
        ]
        patterns["has_acknowledgment"] = any(
            p in response_text.lower() for p in ack_patterns
        )

        # 3. Meta-commentary (thinking about thinking)
        meta_patterns = [
            "let me", "i'll", "first", "to clarify", "breaking this down",
            "in other words", "thinking about"
        ]
        patterns["meta_commentary"] = any(
            p in response_text.lower() for p in meta_patterns
        )

        # 4. Question density (exploration)
        questions = response_text.count("?")
        sentences = len([s for s in response_text.split(".") if s.strip()])
        patterns["question_density"] = questions / sentences if sentences > 0 else 0

        # 5. Structure markers (organization)
        structure_markers = [
            "first", "second", "third", "finally",
            "however", "therefore", "additionally",
            "in contrast", "on the other hand"
        ]
        patterns["structure_markers"] = sum(
            1 for m in structure_markers if m in response_text.lower()
        )

        return patterns

    def detect_claude_failure_modes(self, patterns, metrics):
        """Detect when Claude is exhibiting failure modes"""

        failures = []

        # Overconfident: Low hedges + high certainty
        if patterns["hedge_density"] < 0.01 and metrics["q"] > 0.9:
            failures.append({
                "type": "overconfident",
                "severity": "medium",
                "description": "High certainty without hedging"
            })

        # Robotic: High structure but no acknowledgment
        if patterns["structure_markers"] > 5 and not patterns["has_acknowledgment"]:
            failures.append({
                "type": "robotic",
                "severity": "low",
                "description": "Overly structured, lacks engagement"
            })

        # Circular: High continuity + low TED for multiple turns
        if metrics["continuity"] > 0.8 and metrics["TED"] < 0.10:
            failures.append({
                "type": "circular",
                "severity": "high",
                "description": "Repeating same concepts"
            })

        # Scattered: Many questions + low q
        if patterns["question_density"] > 0.3 and metrics["q"] < 0.5:
            failures.append({
                "type": "scattered_exploration",
                "severity": "medium",
                "description": "Asking questions without synthesis"
            })

        return failures
```

---

## V. Steering: What Actually Works with Claude

### A. System Prompt Modifiers (Most Effective)

**What we learned:** System prompts are SET at conversation start but can include conditional logic.

```python
def generate_regime_aware_system_prompt(base_prompt, expected_regime):
    """
    Generate system prompt with regime-specific guidance
    """

    regime_prompts = {
        "stuck": """
METACOGNITIVE GUIDANCE:
This conversation may converge prematurely. Before settling on answers:
1. Actively consider 2-3 alternative perspectives
2. Explore edge cases that challenge assumptions
3. Ask "what if the opposite were true?"
4. Only synthesize after exploring alternatives
""",

        "scattered": """
METACOGNITIVE GUIDANCE:
This conversation covers many topics. To maintain coherence:
1. Identify common threads across ideas
2. Build explicit connections between concepts
3. Use structure markers (first, second, however, therefore)
4. Summarize periodically
""",

        "exploring": """
METACOGNITIVE GUIDANCE:
This conversation is in healthy exploration mode. Continue:
1. Building on user's concepts while adding new perspectives
2. Maintaining focus while allowing productive tangents
3. Using mid-distance examples (2-3 conceptual hops away)
4. Monitoring for signs of overload
""",
    }

    if expected_regime in regime_prompts:
        return base_prompt + "\n\n" + regime_prompts[expected_regime]
    else:
        return base_prompt
```

**Limitation:** This only works if we can PREDICT the regime before conversation starts. For mid-conversation adjustment, we need different strategies.

### B. In-Conversation Interventions (Constrained)

**What we CAN do mid-conversation:**

```python
class ConversationSteering:
    """Strategies to steer Claude during conversation"""

    def generate_intervention(self, regime, signals, conversation_history):
        """
        Generate intervention based on detected regime
        Returns: Modified user message or system injection
        """

        if regime == "stuck":
            # Inject divergence via devil's advocate question
            return {
                "type": "user_message_modifier",
                "prefix": (
                    "Before you answer, first consider: "
                    "What are 2-3 alternative perspectives on this? "
                    "Then provide your synthesis.\n\n"
                    "Original question: "
                )
            }

        elif regime == "scattered":
            # Request synthesis
            return {
                "type": "explicit_request",
                "message": (
                    "This conversation has covered several topics. "
                    "Can you identify the common threads and "
                    "synthesize what we've learned so far?"
                )
            }

        elif regime == "deep_dive" and signals["continuity"] > 0.8:
            # Check for understanding via perspective shift
            return {
                "type": "user_message_modifier",
                "prefix": (
                    "We've explored this deeply. "
                    "How would you explain this to someone "
                    "approaching it from a different angle?\n\n"
                )
            }

        else:
            return None  # No intervention needed

    def detect_intervention_need(self, regime_history):
        """
        Detect when intervention is needed based on regime persistence
        """
        if len(regime_history) < 3:
            return False

        # Stuck for 3+ turns
        if regime_history[-3:] == ["stuck", "stuck", "stuck"]:
            return True

        # Alternating scattered/stuck (unstable)
        if set(regime_history[-4:]) == {"scattered", "stuck"}:
            return True

        return False
```

---

## VI. Practical Architecture: What to Build Now

### A. Phase 1: Core Measurement (Weeks 1-2)

**Goal:** Build basic graph + metrics from Claude conversations

```python
# adapters/conversation/adapter.py
class ConversationGraphAdapter:
    """
    Builds conversation graph from Claude message stream
    Compatible with existing core/signals.py
    """

    def __init__(self):
        self.node_extractor = ConversationNodeExtractor()
        self.edge_builder = ConversationEdgeBuilder()
        self.graph = nx.DiGraph()
        self.turn_history = []

    def process_turn(self, role, message_text):
        """
        Process one conversation turn
        Returns: (graph, signals)
        """
        # Extract nodes
        nodes = self.node_extractor.extract_nodes(message_text, role)

        # Build edges (within turn + to previous turn)
        prev_nodes = self.turn_history[-1]["nodes"] if self.turn_history else []
        prev_text = self.turn_history[-1]["text"] if self.turn_history else ""

        edges = self.edge_builder.build_edges(
            nodes, prev_nodes, message_text, prev_text
        )

        # Add to graph
        for node in nodes:
            self.graph.add_node(node["id"], **node)
        for edge in edges:
            self.graph.add_edge(edge["source"], edge["target"], **edge)

        # Store turn
        self.turn_history.append({
            "role": role,
            "text": message_text,
            "nodes": nodes,
            "edges": edges,
        })

        # Compute signals (reuse existing core/signals.py)
        signals = self.compute_signals()

        return self.graph, signals

    def compute_signals(self):
        """Compute q, TED, continuity, spread"""
        current_turn = self.turn_history[-1]
        prev_turn = self.turn_history[-2] if len(self.turn_history) > 1 else None

        return {
            "q": compute_q_practical(self.graph, current_turn["nodes"]),
            "TED": compute_TED_practical(
                self.graph,
                self.get_previous_graph() if prev_turn else None
            ),
            "continuity": compute_continuity_practical(
                current_turn["nodes"],
                prev_turn["nodes"] if prev_turn else []
            ),
            "spread": compute_spread_practical(current_turn["nodes"], self.graph),
        }
```

### B. Phase 2: Regime Detection (Week 3)

```python
# Add to adapter
def detect_regime(self, signals):
    """Use regime classifier"""
    classifier = RegimeClassifier()
    regime_info = classifier.classify(signals)

    # Add Claude-specific analysis
    if self.turn_history[-1]["role"] == "assistant":
        behavior = ClaudeBehaviorAnalyzer()
        patterns = behavior.analyze_claude_response(
            self.turn_history[-1]["text"],
            context=self.turn_history
        )
        failures = behavior.detect_claude_failure_modes(patterns, signals)

        regime_info["behavior_patterns"] = patterns
        regime_info["failure_modes"] = failures

    return regime_info
```

### C. Phase 3: MCP Integration (Week 4)

```python
# mcp_server/axiomic_conversation_server.py
from mcp.server import Server
import mcp.types as types

class AxiomicConversationServer(Server):
    """MCP server for Claude conversation monitoring"""

    def __init__(self):
        super().__init__("axiomic-conversation")
        self.adapter = ConversationGraphAdapter()

    @self.call_tool()
    async def call_tool(self, name: str, arguments: dict):
        if name == "analyze_turn":
            return await self.analyze_turn(arguments)
        elif name == "get_regime":
            return await self.get_regime()
        elif name == "get_intervention":
            return await self.get_intervention()

    async def analyze_turn(self, args):
        """Analyze one conversation turn"""
        role = args["role"]  # "user" or "assistant"
        message = args["message"]

        graph, signals = self.adapter.process_turn(role, message)
        regime_info = self.adapter.detect_regime(signals)

        return {
            "signals": signals,
            "regime": regime_info,
            "node_count": len(graph.nodes()),
            "edge_count": len(graph.edges()),
        }

    async def get_regime(self):
        """Get current conversation regime"""
        if not self.adapter.turn_history:
            return {"regime": "initializing"}

        latest_signals = self.adapter.compute_signals()
        return self.adapter.detect_regime(latest_signals)

    async def get_intervention(self):
        """Get steering recommendation"""
        regime_info = await self.get_regime()
        signals = self.adapter.compute_signals()

        steering = ConversationSteering()
        intervention = steering.generate_intervention(
            regime_info["regime"],
            signals,
            self.adapter.turn_history
        )

        return intervention
```

---

## VII. Testing Strategy

### A. Test on This Conversation

```python
# test_meta.py
"""Test conversation adapter on this very conversation"""

def test_on_current_conversation():
    """
    Read this conversation from context
    Run through adapter
    Verify metrics make sense
    """
    adapter = ConversationGraphAdapter()

    # This conversation's turns (simplified)
    turns = [
        ("user", "do you have context of axiomagent project"),
        ("assistant", "[Long response about project structure]"),
        ("user", "analyze the git again/structure..."),
        # ... continue through entire conversation
    ]

    for role, message in turns:
        graph, signals = adapter.process_turn(role, message)
        regime = adapter.detect_regime(signals)

        print(f"Turn {len(adapter.turn_history)}: {role}")
        print(f"  q={signals['q']:.2f}, TED={signals['TED']:.2f}, "
              f"cont={signals['continuity']:.2f}")
        print(f"  Regime: {regime['regime']}")
        print()

    # Expected results for this conversation:
    # - Early: Exploring (moderate TED, building graph)
    # - Middle: Deep dive (focused on axioms, high q)
    # - Late: Pivot (shifted to implementation, TED spike)

    return adapter
```

### B. Calibration Dataset

**Need:** Labeled conversations with known regimes

```python
calibration_data = {
    "stuck_examples": [
        # Conversations that circled without progress
    ],
    "exploring_examples": [
        # Healthy back-and-forth dialogues
    ],
    "scattered_examples": [
        # Conversations that jumped topics too much
    ],
}

def calibrate_thresholds(adapter, labeled_data):
    """
    Find optimal threshold values for regime detection
    """
    from sklearn.metrics import classification_report

    predictions = []
    true_labels = []

    for conversation, label in labeled_data:
        # Run through adapter
        for turn in conversation:
            adapter.process_turn(turn.role, turn.message)

        # Get final regime
        signals = adapter.compute_signals()
        regime = adapter.detect_regime(signals)

        predictions.append(regime["regime"])
        true_labels.append(label)

    # Evaluate
    print(classification_report(true_labels, predictions))

    # Tune thresholds to maximize accuracy
    # ... grid search over threshold values
```

---

## VIII. Key Insights: Theory vs Practice

### What Works from v3 Spec

✅ **Graph-based representation**
- Text CAN be parsed into nodes and edges
- Semantic embeddings provide measurable similarity

✅ **Core metrics (q, TED, continuity)**
- Computable from text features
- Correlate with observable conversation quality

✅ **Regime detection**
- Text patterns DO cluster into detectable regimes
- Stuck, exploring, scattered are distinguishable

### What Needs Adaptation

⚠️ **"Emotion weight" is hard**
- Sentiment analysis from text is noisy
- Better: Track hedge density, certainty markers

⚠️ **"Trust weight" requires external data**
- Can't assess claim truthfulness from text alone
- Better: Track citation patterns, epistemic markers

⚠️ **Real-time steering is constrained**
- System prompts are set at start
- Mid-conversation: rely on explicit requests

⚠️ **Multi-party is harder**
- Speaker attribution essential
- Need conversation structure (who replies to whom)

### What's Actually Feasible Now

**High confidence (build this):**
1. Basic graph construction from Claude messages
2. q, TED, continuity, spread metrics
3. Stuck/exploring/scattered regime detection
4. Post-hoc conversation analysis and reporting

**Medium confidence (prototype):**
1. Claude behavior pattern detection
2. Failure mode identification
3. Intervention suggestions
4. MCP server integration

**Low confidence (future work):**
1. Real-time steering during generation
2. Multi-party conversation analysis
3. Cross-modal (text + tone) analysis
4. Predictive regime forecasting

---

## IX. Recommended Implementation Path

### Week 1: Core Graph + Metrics
- Implement `ConversationNodeExtractor`
- Implement `ConversationEdgeBuilder`
- Compute q, TED, continuity on test data
- Validate against manual inspection

### Week 2: Regime Detection
- Implement `RegimeClassifier`
- Implement `ClaudeBehaviorAnalyzer`
- Test on this conversation (meta-test)
- Calibrate thresholds

### Week 3: MCP Server
- Build basic MCP tools
- Integrate with Claude Code
- Test in real usage
- Gather feedback data

### Week 4: Iteration
- Refine thresholds based on usage
- Add intervention strategies
- Build reporting/visualization
- Document learnings

---

## X. Success Criteria

**Phase 1 Success:**
- Adapter processes 100+ turn conversation without errors
- Metrics produce interpretable values (not all 0.5)
- Can identify at least 2 distinct regimes in test data

**Phase 2 Success:**
- Regime detection accuracy >70% on labeled data
- Can detect "stuck" conversations with >80% precision
- Users report metrics are meaningful

**Phase 3 Success:**
- MCP server responds <200ms
- Integration with Claude Code works smoothly
- Interventions lead to measurable metric improvements

---

## Conclusion

The v3 design spec is **theoretically sound** but needs **practical grounding** in what's observable from Claude text. This document provides:

1. **Realistic node/edge extraction** from text
2. **Computable metrics** from semantic features
3. **Detectable regimes** from text patterns
4. **Feasible interventions** within API constraints
5. **Concrete implementation path** for building it

**The core insight:** We can't read Claude's mind, but we can measure the conversation graph that emerges from the interaction, and that's enough to detect and steer toward healthy dialogue.

Start with Phase 1, validate on this conversation, iterate based on real usage.

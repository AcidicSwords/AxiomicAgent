# Communication Theory Through the Axiomic Lens
## Linguistics, Debate, De-escalation, and LLM Equivalents

**Version:** 1.0
**Date:** 2025-01-07
**Purpose:** Map communication patterns to graph metrics and LLM behavior

---

## Executive Summary

Communication patterns across linguistics, debate, therapy, and negotiation share underlying graph structures. The same metrics that analyze curricula (q, TED, continuity) capture conversational health, argumentative rigor, and de-escalation dynamics.

**Core Finding:** Every communication pattern has a graph signature and ML equivalent.

---

## I. Linguistics & Pragmatics

### A. Speech Acts (Austin 1962, Searle 1969)

**Theory:** Utterances perform actions—assert, request, promise, apologize.

**Axiomic Mapping:**

```python
# Speech act = node type in conversation graph
node_types = {
    "assertion": {"creates_edges": True, "TED_impact": "low"},
    "question": {"creates_edges": True, "TED_impact": "high"},  # Opens space
    "answer": {"creates_edges": True, "TED_impact": "low"},     # Closes space
    "command": {"creates_edges": False, "TED_impact": "medium"},
    "apology": {"creates_edges": True, "TED_impact": "low"},    # Repairs edges
}

# Quality of speech act = appropriateness in context
q(speech_act) = felicity_conditions_met / total_conditions

# Example:
q("promise") = (speaker_intends + speaker_able + hearer_wants) / 3
```

**LLM Equivalent:**

```python
# LLM response type classification
class ResponseTypeClassifier:
    """Classify LLM output by speech act"""

    patterns = {
        "assertion": r"^(This is|It's|The|.*\.)",
        "question": r"^(What|How|Why|Do you|\?)",
        "hedge": r"(might|could|perhaps|possibly)",
        "meta-comment": r"(Let me|I'll|Before we)",
    }

    def classify(self, response):
        # Returns dominant speech act
        # High assertion + low question = converging
        # High question + low assertion = exploring
        pass

# Stuck conversation = too many assertions, not enough questions
if assertion_ratio > 0.8:
    regime = "stuck"  # Premature convergence
```

**Conversation Adapter Impact:**
- **Nodes:** Tag with speech act type
- **Edges:** Questions open divergent edges, assertions create convergent edges
- **q:** High when speech acts are contextually appropriate

---

### B. Turn-Taking (Sacks, Schegloff, Jefferson 1974)

**Theory:** Conversation has systematic turn allocation—current speaker selects next, or self-selection, or current continues.

**Axiomic Mapping:**

```python
# Turn = step in conversation graph
# Smooth turn-taking = high continuity (concepts carry over)
# Interruption = TED spike (abrupt topic shift)

turn_transition_quality = {
    "smooth_handoff": {"continuity": 0.6, "TED": 0.1},
    "topic_shift": {"continuity": 0.3, "TED": 0.4},
    "interruption": {"continuity": 0.1, "TED": 0.7},
    "return_to_topic": {"continuity": 0.5, "TED": 0.2},
}

# Adjacency pairs (question→answer, greeting→greeting)
adjacency_pair_quality = overlap(turn_n_concepts, turn_n+1_concepts)
```

**LLM Equivalent:**

```python
# User message → LLM response coherence
coherence = cosine_similarity(
    embed(user_message),
    embed(llm_response)
)

# High coherence = smooth turn-taking
# Low coherence = topic drift (possibly stuck, possibly exploring)

# Conversation adapter measures this as continuity:
continuity = |concepts(user) ∩ concepts(assistant)| / union
```

**Conversation Adapter Impact:**
- **Continuity:** Measures turn coherence
- **TED:** Detects topic shifts vs smooth transitions
- **Edges:** User→assistant reply chains

---

### C. Gricean Maxims (Grice 1975)

**Theory:** Cooperative principle with maxims—quantity, quality, relevance, manner.

**Axiomic Mapping:**

| Maxim | Axiomic Metric | Graph Property | LLM Failure Mode |
|-------|----------------|----------------|------------------|
| **Quantity** (be informative) | Edge density | Too few edges = underinformative | Terse responses when detail needed |
| **Quality** (be truthful) | q (edge quality) | Low q = unverified claims | Hallucination, false confidence |
| **Relevance** (be pertinent) | Continuity | Low continuity = off-topic | Topic drift, ignoring user intent |
| **Manner** (be clear) | Graph modularity | High spread = unclear | Scattered, unfocused response |

**Implementation:**

```python
# Gricean violation detector
def detect_violations(response_graph, context_graph):
    violations = {}

    # Quantity: Too little information
    if len(response_graph.nodes) < 5:
        violations["quantity_min"] = "Underinformative"
    # Too much information
    if len(response_graph.nodes) > 50:
        violations["quantity_max"] = "Overwhelming"

    # Quality: Low edge quality (unverified claims)
    if mean(q(e) for e in response_graph.edges) < 0.5:
        violations["quality"] = "Unsubstantiated claims"

    # Relevance: Low continuity with context
    cont = continuity(response_graph, context_graph)
    if cont < 0.3:
        violations["relevance"] = "Off-topic response"

    # Manner: High spread (unclear)
    if spread(response_graph) > 0.7:
        violations["manner"] = "Unfocused, scattered"

    return violations
```

**LLM Equivalent:**
- **Quantity:** Token count, concept count
- **Quality:** Confidence scores, citation presence
- **Relevance:** Embedding similarity to user query
- **Manner:** Perplexity, sentence structure complexity

**Conversation Adapter Impact:**
- Maxim violations = specific resistance patterns
- Can diagnose WHY conversation is stuck

---

## II. Communication Theory

### A. Shannon Information Theory (1948)

**Theory:** Communication = transmitter → channel (with noise) → receiver

**Axiomic Mapping:**

```python
# Information content = surprise = -log P(message | context)
# High surprise = high TED (unexpected concept shift)
# Low surprise = low TED (expected continuation)

# Channel capacity = maximum TED sustainable without confusion
# If TED > channel_capacity → saturated (overwhelmed)

# Redundancy = continuity
# Necessary to overcome noise (measurement resistance R^meas)

channel_model = {
    "capacity": "max_TED_tolerable",  # ~0.5 for most conversations
    "noise": "R_meas",                # Ambiguity, unclear language
    "redundancy": "continuity",       # Repetition for clarity
    "bandwidth": "concepts_per_turn", # Limited by working memory
}
```

**LLM Equivalent:**

```python
# LLM uncertainty = entropy of token distribution
H(next_token | context) = -Σ p(t) log p(t)

# High entropy = high TED (model uncertain, exploring)
# Low entropy = low TED (model confident, converging)

# Conversation stuck when:
# - Entropy very low (deterministic responses)
# - TED very low (no new information)
# - Both indicate premature convergence

def detect_premature_convergence(llm_probs, graph):
    entropy = compute_entropy(llm_probs)
    ted = compute_TED(graph)

    if entropy < 0.5 and ted < 0.15:
        return "stuck"  # Model too confident, graph not evolving
```

**Conversation Adapter Impact:**
- TED ≈ information content
- High TED + high noise (R^meas) = confusion
- Optimal: moderate TED, low noise

---

### B. Feedback Loops

**Theory:** Communication requires feedback (acknowledgment, clarification)

**Axiomic Mapping:**

```python
# Positive feedback loop = increasing TED (divergence, potentially scattered)
# Negative feedback loop = decreasing TED (convergence, potentially stuck)
# Healthy conversation = oscillation between exploration and consolidation

feedback_patterns = {
    "acknowledgment": {
        "effect": "stabilizes continuity",
        "edge_type": "reinforcing",
        "example": "I see, so you're saying..."
    },
    "clarification_request": {
        "effect": "increases TED (opens new angle)",
        "edge_type": "exploring",
        "example": "Could you elaborate on X?"
    },
    "challenge": {
        "effect": "high TED spike",
        "edge_type": "pivot",
        "example": "But what about contradictory case Y?"
    },
    "summary": {
        "effect": "increases q (consolidation)",
        "edge_type": "synthesizing",
        "example": "To summarize, we've covered..."
    }
}
```

**LLM Equivalent:**

```python
# LLM metacognitive feedback
class FeedbackInjector:
    """Inject feedback based on conversation state"""

    def generate_feedback(self, signals):
        if signals.TED < 0.15:
            # Stuck → inject divergence via clarification
            return "Before I conclude, let me check: have we considered...?"

        elif signals.TED > 0.5:
            # Scattered → synthesize via summary
            return "Let me tie these threads together..."

        elif signals.q > 0.85:
            # Converging → challenge assumption
            return "One potential counterpoint to consider..."

        else:
            # Optimal → acknowledge
            return "Building on that point..."
```

**Conversation Adapter Impact:**
- Tag messages by feedback type
- Track feedback loops (ACK → CONTINUE vs CHALLENGE → PIVOT)
- Detect missing feedback (no acknowledgment = low continuity)

---

## III. Debate & Argumentation

### A. Toulmin Model (1958)

**Theory:** Argument = Claim + Data + Warrant (+ Backing + Qualifier + Rebuttal)

**Axiomic Mapping:**

```python
# Argument = subgraph with specific structure
argument_graph = {
    "claim": "target node",
    "data": "source nodes (evidence)",
    "warrant": "edges from data → claim",
    "backing": "meta-edges supporting warrant quality",
    "qualifier": "q(warrant) ∈ [0,1]",  # certainly, probably, possibly
    "rebuttal": "alternative paths to ¬claim"
}

# Strong argument = high TED_τ(data → claim)
# Weak argument = low TED_τ (no verified path)

# Debate quality = number of well-structured argument subgraphs
debate_quality = Σ q(argument_i) / num_claims
```

**LLM Equivalent:**

```python
# LLM argumentation structure
class ArgumentAnalyzer:
    """Analyze argument structure in LLM responses"""

    def extract_argument(self, response):
        # Parse for claim
        claim = find_thesis_statement(response)

        # Find supporting evidence
        evidence = find_citations_or_examples(response)

        # Measure warrant strength
        warrant_strength = semantic_similarity(evidence, claim)

        # Detect qualifiers (certainty)
        qualifier = count_hedge_words(response) / word_count

        return {
            "claim": claim,
            "data": evidence,
            "warrant_q": warrant_strength,
            "qualifier": qualifier,
            "has_rebuttal": contains_counterargument(response)
        }

# Stuck in debate = repeating same argument (low TED)
# Productive debate = new arguments added (moderate TED)
# Scattered debate = too many unconnected claims (high TED, low q)
```

**Conversation Adapter Impact:**
- Nodes = claims and evidence
- Edges = warrant connections
- Edge quality = strength of inference
- High-quality debate = multiple argument subgraphs with high internal q

---

### B. Dialectic (Thesis-Antithesis-Synthesis)

**Theory:** Progress through opposition and resolution

**Axiomic Mapping:**

```python
# Dialectical progression:
#
# Phase 1: Thesis (initial claim)
#   - Low TED (single perspective)
#   - Moderate q (coherent but limited)
#
# Phase 2: Antithesis (counterpoint)
#   - HIGH TED (contradictory concepts introduced)
#   - Low q initially (opposing views not integrated)
#
# Phase 3: Synthesis (resolution)
#   - Moderate TED (new framework)
#   - HIGH q (contradictions resolved)
#   - High continuity (preserves valid parts of both)

dialectic_signature = [
    {"phase": "thesis", "q": 0.7, "TED": 0.1, "continuity": 0.0},
    {"phase": "antithesis", "q": 0.4, "TED": 0.6, "continuity": 0.2},
    {"phase": "synthesis", "q": 0.8, "TED": 0.3, "continuity": 0.5},
]

# Premature convergence = skipping antithesis
# Stuck in antithesis = can't synthesize (low q persists)
```

**LLM Equivalent:**

```python
# LLM dialectic detector
def detect_dialectic_phase(conversation_history):
    recent_TED = [compute_TED(step) for step in last_N_steps]
    recent_q = [compute_q(step) for step in last_N_steps]

    # Thesis: stable, coherent
    if mean(recent_TED) < 0.2 and mean(recent_q) > 0.65:
        return "thesis"

    # Antithesis: disruptive, contradictory
    if max(recent_TED) > 0.5 and min(recent_q) < 0.5:
        return "antithesis"

    # Synthesis: stabilizing at higher level
    if recent_TED[-1] < 0.3 and recent_q[-1] > 0.75 and prev_phase == "antithesis":
        return "synthesis"

    return "unclear"

# Guidance:
if phase == "thesis" and duration > threshold:
    return "inject_antithesis"  # Prevent premature convergence
elif phase == "antithesis" and duration > threshold:
    return "attempt_synthesis"  # Help resolve
```

**Conversation Adapter Impact:**
- Track phase transitions (TED spikes = antithesis moments)
- Detect when synthesis is needed (sustained low q)
- Encourage dialectic when conversation too smooth (stuck)

---

## IV. De-escalation & Conflict Resolution

### A. Active Listening

**Theory:** Acknowledge, reflect, validate to build rapport

**Axiomic Mapping:**

```python
# Active listening = high continuity (concepts echoed back)
#                  + low TED (not introducing new conflict)
#                  + increasing q (building shared understanding)

active_listening_signature = {
    "acknowledgment": {
        "continuity": 0.8,  # Repeat partner's concepts
        "TED": 0.1,         # Don't shift topic
        "q_delta": +0.1,    # Increase coherence
    },
    "reflection": {
        "continuity": 0.7,  # Paraphrase
        "TED": 0.15,        # Slight reframing
        "q_delta": +0.15,   # Clarify understanding
    },
    "validation": {
        "continuity": 0.6,  # Connect to shared values
        "TED": 0.2,         # Broader context
        "q_delta": +0.2,    # Strengthen edges
    }
}

# De-escalation succeeds when:
# - TED decreases (less conflict, more alignment)
# - q increases (shared understanding emerges)
# - continuity stays high (mutual concepts maintained)
```

**LLM Equivalent:**

```python
# LLM de-escalation via continuity
class DeescalationStrategy:
    """Use continuity to de-escalate"""

    def generate_deescalating_response(self, user_message, context):
        # Extract user's concepts
        user_concepts = extract_concepts(user_message)

        # Build response that:
        # 1. Echoes user concepts (high continuity)
        # 2. Doesn't introduce conflict (low TED)
        # 3. Adds integrating framework (increase q)

        response_template = {
            "acknowledgment": f"I hear that you're concerned about {user_concepts}",
            "reflection": f"It sounds like the key issue is {reframe(user_concepts)}",
            "validation": f"That's a valid point about {shared_value(user_concepts)}",
            "bridge": f"Perhaps we can find common ground in {synthesis}"
        }

        return response_template

# Escalation = increasing TED without increasing q
# De-escalation = maintaining continuity while increasing q
```

**Conversation Adapter Impact:**
- Track emotional temperature via TED spikes
- De-escalation = intentionally high continuity responses
- Success = TED↓ and q↑ over time

---

### B. Finding Common Ground

**Theory:** Identify shared interests/values to resolve conflict

**Axiomic Mapping:**

```python
# Common ground = nodes present in both parties' graphs
common_ground = user_graph.nodes ∩ assistant_graph.nodes

# Conflict = disconnected subgraphs
# Resolution = building edges between subgraphs

def find_bridge_concepts(graph_A, graph_B):
    """Find concepts that connect conflicting positions"""

    # Look for nodes at moderate distance from both
    # (mid-distance optimality - Axiom 9)

    bridge_candidates = []
    for node in all_concepts:
        dist_A = shortest_path(graph_A_nodes, node)
        dist_B = shortest_path(graph_B_nodes, node)

        if 2 <= dist_A <= 4 and 2 <= dist_B <= 4:
            # Mid-distance from both = potential bridge
            bridge_candidates.append(node)

    return bridge_candidates

# Introduce bridge concepts to increase q without forcing agreement
```

**LLM Equivalent:**

```python
# LLM bridge-building
class BridgeBuilder:
    """Find connecting concepts between positions"""

    def build_bridge(self, position_A, position_B):
        # Embed both positions
        emb_A = embed(position_A)
        emb_B = embed(position_B)

        # Find concepts at intermediate distance
        # (not in either position, but related to both)

        candidates = concept_database
        mid_distance_concepts = [
            c for c in candidates
            if 0.3 < cosine(c, emb_A) < 0.7 and
               0.3 < cosine(c, emb_B) < 0.7
        ]

        # Use these to frame synthesis
        return f"Both perspectives relate to {mid_distance_concepts}..."

# This is Axiom 9 applied to conflict resolution
# Don't force agreement (distance 0) or stay apart (distance ∞)
# Find mid-distance bridges
```

**Conversation Adapter Impact:**
- Detect conflicting subgraphs (low edge density between them)
- Identify bridge nodes (moderate distance from both)
- Suggest mid-distance concepts for synthesis

---

## V. Context-Specific Patterns

### A. Academic Discourse

**Pattern:** Heavy citation, hedging, conditional claims

**Graph Signature:**

```python
academic_pattern = {
    "nodes": ["citations", "prior_work", "claims", "evidence"],
    "edges": "citation → claim (warrant)",
    "q": "high (rigorous inference)",
    "TED": "low-moderate (incremental contributions)",
    "continuity": "very high (build on literature)",
    "spread": "low (focused on narrow problem)",
}

# Key markers:
# - High citation density (many edges to external nodes)
# - Hedge words (reduce q deliberately: "possibly", "suggest")
# - Conditional framing (if-then edges)

def detect_academic_mode(text):
    markers = {
        "citations": count_patterns(r'\([A-Z][a-z]+,? \d{4}\)'),
        "hedges": count_words(["possibly", "likely", "suggest", "may"]),
        "conditionals": count_words(["if", "assuming", "given"]),
    }
    return sum(markers.values()) > threshold
```

**LLM Equivalent:**

```python
# LLM academic style
# - Should maintain high continuity (cite prior work)
# - Should use hedges (reduce false confidence)
# - Should limit TED (focused contributions)

if context == "academic":
    guidance = {
        "continuity_target": 0.7,  # Always reference prior
        "TED_max": 0.3,            # Stay focused
        "require_hedges": True,    # Conditional claims
        "citation_density_min": 3, # Per response
    }
```

---

### B. Therapy/Counseling

**Pattern:** Validation, reflection, gradual exploration

**Graph Signature:**

```python
therapy_pattern = {
    "therapist_continuity": 0.9,  # Echo client concepts
    "therapist_TED": 0.1,          # Don't lead, follow
    "client_TED": "variable",      # Client explores
    "q": "increases slowly",       # Build coherence gently
    "intervention": "when q plateaus, gentle TED increase"
}

# Rogerian reflection = perfect continuity
# "You're saying X" where X ∈ client_concepts

# Interpretation = moderate TED increase
# "Could this relate to Y?" where Y is mid-distance from X
```

**LLM Equivalent:**

```python
# Therapeutic LLM behavior
class TherapeuticAdapter:
    def generate_response(self, client_message, context):
        # First: validate (high continuity)
        client_concepts = extract(client_message)
        validation = f"I hear that {client_concepts}..."

        # If client is stuck (low client TED over time):
        if client_stuck:
            # Gently inject mid-distance question
            bridge = find_mid_distance_concept(client_concepts)
            exploration = f"I wonder if this connects to {bridge}?"

        # If client is scattered (high TED, low q):
        if client_scattered:
            # Help synthesize
            synthesis = "There seems to be a common thread: {find_pattern}..."

        return validation + optional_exploration
```

---

### C. Negotiation

**Pattern:** Positions → interests → options → agreement

**Graph Signature:**

```python
negotiation_phases = {
    "positions": {
        "q": 0.9,  # Each party coherent internally
        "TED": 0.0,  # No overlap initially
        "continuity": 0.0,  # Disconnected graphs
    },
    "interests": {
        "q": 0.6,  # Exploring underlying needs
        "TED": 0.3,  # Finding connections
        "continuity": 0.3,  # Shared concepts emerge
    },
    "options": {
        "q": 0.5,  # Many possibilities
        "TED": 0.4,  # Creative exploration
        "continuity": 0.5,  # Building on shared interests
    },
    "agreement": {
        "q": 0.85,  # Coherent solution
        "TED": 0.2,  # Stable
        "continuity": 0.7,  # Integrates both interests
    }
}

# Stuck negotiation = staying in positions (TED = 0)
# Successful negotiation = progression through phases (TED increases then stabilizes)
```

**LLM Equivalent:**

```python
# LLM negotiation support
def negotiation_guidance(phase, signals):
    if phase == "positions" and signals.TED < 0.1:
        # Stuck in positions → shift to interests
        return "Let's explore the underlying interests. What's important to you about this?"

    elif phase == "interests" and signals.continuity > 0.4:
        # Shared interests found → generate options
        return "Given these shared interests, what options might work?"

    elif phase == "options" and signals.q < 0.5:
        # Too scattered → focus
        return "Which of these options best addresses our core interests?"

    elif signals.q > 0.8 and signals.TED < 0.25:
        # Converging → check for agreement
        return "It sounds like we're aligning on..."
```

---

## VI. LLM-Specific Patterns

### A. Premature Convergence in LLMs

**Problem:** LLMs often give confident answer without exploring alternatives

**Axiomic Signature:**
```python
premature_convergence = {
    "q": 0.9,  # Very coherent (single perspective)
    "TED": 0.05,  # Almost no concept change
    "continuity": 0.85,  # Repeating same concepts
    "entropy": 0.3,  # Low token-level uncertainty
}

# Human would say: "But what about...?"
# LLM says: "Therefore, the answer is X."

# Detection:
if q > 0.85 and TED < 0.15 and continuity > 0.7:
    # Inject divergence BEFORE completing response
    metacognitive_injection = """
    WAIT: Before concluding, consider:
    - What edge cases challenge this?
    - What alternative framings exist?
    - What am I assuming?
    """
```

**Prevention:**
```python
# During generation, if premature convergence detected:
# 1. Increase temperature (↑ entropy)
# 2. Inject counter-prompt ("What if the opposite?")
# 3. Sample mid-distance concepts
# 4. Only then synthesize
```

---

### B. Hallucination as Low-Quality Edges

**Problem:** LLMs create false connections

**Axiomic Diagnosis:**
```python
# Hallucination = edge with low quality
# q(e) = verification_score

hallucination_edge = {
    "source": "real_concept",
    "target": "plausible_but_false_concept",
    "q": 0.1,  # Very low (unverified)
    "weight": 1.0,  # But presented confidently
}

# System-level TED_τ drops when many low-q edges
TED_τ = #{verified_paths} / #{all_paths}

# If TED_τ < 0.5 → many unverified claims
```

**Detection & Mitigation:**
```python
def detect_hallucination_risk(response_graph):
    # Count edges without support
    unsupported = [e for e in response_graph.edges if q(e) < 0.4]

    if len(unsupported) / len(response_graph.edges) > 0.3:
        return {
            "risk": "high",
            "intervention": "Request citations or hedge claims"
        }

    # Low-quality edges = resistance (R^edge)
    R_edge = 1 - mean_quality(response_graph)

    if R_edge > 0.6:
        return "Too many unverified connections"
```

---

## VII. Synthesis: Conversation Adapter Design

### Universal Communication Metrics

Based on this analysis, the conversation adapter should track:

| Metric | Communication Analog | Healthy Range | Stuck Indicator | Scattered Indicator |
|--------|---------------------|---------------|-----------------|---------------------|
| **q** | Coherence, focus | 0.65-0.85 | >0.85 | <0.5 |
| **TED** | Topic shift, information | 0.15-0.35 | <0.15 | >0.5 |
| **continuity** | Turn coherence, memory | 0.3-0.6 | >0.7 | <0.2 |
| **spread** | Focus vs scattered | 0.3-0.6 | <0.3 | >0.7 |
| **TED_τ** | Verified connections | >0.6 | Any | <0.4 |

### Node Types for Conversation

```python
node_types = {
    "concept": "Core idea mentioned",
    "claim": "Assertion made",
    "evidence": "Supporting fact/example",
    "question": "Open exploration",
    "acknowledgment": "Validation/agreement",
    "hedge": "Qualification/uncertainty",
    "rebuttal": "Counter-argument",
}
```

### Edge Types

```python
edge_types = {
    "co-mention": "Terms appear in same message",
    "reply": "User concept → assistant concept",
    "warrant": "Evidence → claim",
    "contradiction": "Opposing claims",
    "synthesis": "Resolution of contradiction",
}
```

### Quality Computation

```python
def compute_edge_quality(edge, conversation_context):
    """
    Multi-factor edge quality for conversation
    """
    q_components = {}

    # Frequency: How often do these concepts co-occur?
    q_components["frequency"] = edge.weight / max_weight

    # Recency: Recent edges are higher quality (working memory)
    q_components["recency"] = 1.0 if edge.last_seen == current_step else 0.7

    # Mutual information: How specific is this connection?
    q_components["mutual_info"] = pmi(edge.source, edge.target)

    # Verification: Is this connection supported?
    # (For LLMs: check if claim has evidence)
    q_components["verification"] = has_support(edge)

    # Weighted combination
    q = (
        0.3 * q_components["frequency"] +
        0.2 * q_components["recency"] +
        0.3 * q_components["mutual_info"] +
        0.2 * q_components["verification"]
    )

    return clip(q, 0, 1)
```

---

## VIII. Implementation Roadmap

### Phase 1: Basic Conversation Adapter
- Extract concepts from messages
- Build co-mention graph
- Compute q, TED, continuity using existing `core/signals.py`

### Phase 2: Communication-Specific Features
- Tag nodes by type (claim, evidence, question)
- Tag edges by type (reply, warrant, contradiction)
- Implement context-sensitive quality

### Phase 3: Pattern Detection
- Detect dialectic phases
- Detect de-escalation/escalation
- Detect premature convergence
- Detect hallucination risk

### Phase 4: Context Adaptation
- Academic mode (high citation density)
- Therapy mode (high continuity)
- Debate mode (argument structure)
- Negotiation mode (phase progression)

---

## IX. Key Insights

1. **Communication IS graph dynamics**
   Every communication theory maps to graph operations

2. **Premature convergence is universal**
   Across debate, therapy, negotiation: getting stuck = low TED + high q

3. **LLMs replicate human patterns**
   Hallucination = low-quality edges
   Overconfidence = premature convergence
   Scattered responses = high TED + low q

4. **Metacognition is conversation repair**
   Active listening = intentional high continuity
   Dialectic = managed TED oscillation
   De-escalation = TED reduction while increasing q

5. **Context changes thresholds, not structure**
   Academic: continuity_target = 0.7
   Therapy: therapist_TED_max = 0.15
   Debate: optimal_TED = 0.3-0.5
   **But all use same metrics**

---

## X. Next Steps

1. Implement conversation adapter with basic graph building
2. Test on this conversation (meta-test)
3. Calibrate thresholds from real data
4. Add communication-specific quality factors
5. Build context-aware guidance

**The conversation adapter is now theoretically grounded across multiple disciplines.**

---

## References

- Austin, J.L. (1962). *How to Do Things with Words*
- Grice, H.P. (1975). *Logic and Conversation*
- Toulmin, S. (1958). *The Uses of Argument*
- Sacks, H. et al. (1974). *A Simplest Systematics for Turn-Taking*
- Shannon, C. (1948). *A Mathematical Theory of Communication*
- Searle, J. (1969). *Speech Acts*

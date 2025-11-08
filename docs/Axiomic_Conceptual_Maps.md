# Axiomic Conceptual Maps & Visual Guides

**Visual representations of cross-disciplinary connections**

---

## I. The Central Insight (Conceptual Diagram)

```
                    AXIOMIC SUBSTRATE
                    (Graph Metrics)
                           |
              ┌────────────┼────────────┐
              ↓            ↓            ↓
           q (cohesion) TED (drift) continuity
              ↓            ↓            ↓
    ┌─────────┴─────────┬──┴──┬────────┴─────────┐
    ↓                   ↓     ↓                  ↓
COGNITION          NEUROSCIENCE  PHILOSOPHY   MEMORY
Schema             Functional    Justified    Hebbian
Integration        Connectivity  Belief       Learning
    ↓                   ↓     ↓                  ↓
PSYCHOLOGY            ML        INFRASTRUCTURE
ZPD & Learning    Meta-Learning  System Health
Trajectories      Curriculum     Monitoring

ALL VIEW THE SAME STRUCTURE THROUGH DIFFERENT LENSES
```

---

## II. The Metric Rosetta Stone

### How Each Discipline Interprets the Universal Metrics

```
q (Quality/Cohesion) = [0, 1]
├─ Cognitive Science: Schema coherence
├─ Neuroscience: Functional connectivity strength
├─ Philosophy: Coherentist justification
├─ Psychology: Cognitive load inverse
├─ Memory: Consolidation strength
├─ ML: Representation quality
└─ Infrastructure: System health

TED (Drift/Change) = [0, 1]
├─ Cognitive Science: Conceptual shift magnitude
├─ Neuroscience: Phase transition
├─ Philosophy: Belief revision
├─ Psychology: Learning rate
├─ Memory: Forgetting rate
├─ ML: Gradient magnitude
└─ Infrastructure: State change

continuity = [0, 1]
├─ Cognitive Science: Retrieval cue overlap
├─ Neuroscience: Hebbian co-activation
├─ Philosophy: Justification chain
├─ Psychology: Spacing effect
├─ Memory: Synaptic persistence
├─ ML: Transfer learning
└─ Infrastructure: Data lineage

TED_τ (Trusted Path Density) = [0, 1]
├─ Cognitive Science: Knowledge accessibility
├─ Neuroscience: Effective connectivity
├─ Philosophy: Justified true belief
├─ Psychology: Transfer learning success
├─ Memory: Recall probability
├─ ML: Generalization
└─ Infrastructure: Service reachability
```

---

## III. The Learning Phase Diagram

```
         HIGH TED (Change)
              ↑
              |
    SCATTERED |  PIVOT
    (Chaotic) |  (Major shift)
              |
    ─ ─ ─ ─ ─ + ─ ─ ─ ─ ─ → HIGH q (Coherence)
              |
    EXPLORING |  STUCK
    (Optimal) |  (Converged)
              |
         LOW TED
```

### Quadrant Descriptions

**EXPLORING (Low-mid TED, Mid-high q):**
- **Status**: Optimal learning zone
- **Action**: Continue
- **Analogy**: ZPD (Vygotsky), Criticality (neuroscience), Flow state

**STUCK (Low TED, High q):**
- **Status**: Premature convergence
- **Action**: Inject divergence
- **Analogy**: Local minimum, Echo chamber, Overfitting

**PIVOT (High TED, Mid continuity):**
- **Status**: Major transition
- **Action**: Acknowledge shift, bridge contexts
- **Analogy**: Paradigm shift, Phase transition, Mode change

**SCATTERED (High TED, Low q):**
- **Status**: Lost coherence
- **Action**: Synthesize, focus
- **Analogy**: Cognitive overload, Fragmentation, Noise

---

## IV. The Pipeline Architecture (Layer View)

```
┌─────────────────────────────────────────────────────┐
│ Layer 5: LLM AGENT                                  │
│ ↑ Contract: Safety, coherence                       │
│ │ Arbiter: Metacognitive guidance                   │
├─┴───────────────────────────────────────────────────┤
│ Layer 4: REPORTERS                                  │
│ ↑ Contract: JSON schema, interpretability           │
│ │ Arbiter: Reporter type (insight/dynamics)         │
├─┴───────────────────────────────────────────────────┤
│ Layer 3: CORE ENGINE                                │
│ ↑ Contract: 0 ≤ signals ≤ 1, step sequence         │
│ │ Arbiter: Core config (heads, spread, locality)    │
├─┴───────────────────────────────────────────────────┤
│ Layer 2: ADAPTER                                    │
│ ↑ Contract: Valid graph, step features              │
│ │ Arbiter: Preprocessor config (filters, weights)   │
├─┴───────────────────────────────────────────────────┤
│ Layer 1: BUILDER                                    │
│ ↑ Contract: nodes.csv + edges.csv schema            │
│ │ Arbiter: Builder params (profile, step_semantics) │
├─┴───────────────────────────────────────────────────┤
│ Layer 0: RAW DATA (HTML, transcripts, logs)        │
└─────────────────────────────────────────────────────┘

Each ↑ is a HANDOFF CONTRACT (Axiom 6):
  I = Invariants (must preserve)
  A = Admissible changes (may vary)
  Λ = Latency constraints
  J = Arbiter (conflict resolution)
```

---

## V. The Resistance Decomposition Triangle

```
           TOTAL RESISTANCE
                  /\
                 /  \
                /    \
               /      \
              /        \
             /          \
            /            \
           /   R^model    \
          /   (closure)    \
         /                  \
        /____________________\
       R^meas              R^edge
      (sensors)          (connectivity)

DIAGNOSIS:
1. Measure all three
2. Fix dominant component
3. Re-measure

INTERVENTIONS:
R^meas → Upgrade measurement
R^model → Change representation/regime
R^edge → Build connections, raise TED_τ
```

---

## VI. The Metacognitive Decision Tree

```
START: Analyze current step
  ├─ Compute: q, TED, continuity
  │
  ├─ q > 0.85 AND TED < 0.15 AND cont > 0.5?
  │   YES → STUCK
  │   │  └─ Action: Inject divergence
  │   │     - Sample mid-distance from current focus
  │   │     - Ask "what if?" questions
  │   │     - Explore alternatives
  │   NO ↓
  │
  ├─ q > 0.65 AND TED < 0.25 AND 0.2 < cont < 0.6?
  │   YES → DEEPENING
  │   │  └─ Action: Continue, monitor for convergence
  │   NO ↓
  │
  ├─ 0.4 < q < 0.7 AND 0.2 < TED < 0.5?
  │   YES → EXPLORING (OPTIMAL)
  │   │  └─ Action: Continue current approach
  │   NO ↓
  │
  ├─ q < 0.4 AND TED > 0.4 AND cont < 0.3?
  │   YES → SCATTERED
  │   │  └─ Action: Synthesize and focus
  │   │     - Identify common threads
  │   │     - Build bridging connections
  │   NO ↓
  │
  ├─ TED > 0.5?
  │   YES → PIVOT
  │   │  └─ Action: Acknowledge transition
  │   │     - Bridge to prior context
  │   │     - Prepare for new phase
  │   NO ↓
  │
  └─ MIXED
     └─ Action: Continue, observe trends
```

---

## VII. Domain Concept Mapping

### The Same Pattern Across Disciplines

```
┌─────────────────────────────────────────────────────┐
│                   GRAPH SUBSTRATE                    │
│              Nodes + Edges + q(e) + TED              │
└──────────────────┬──────────────────────────────────┘
                   │
        ┌──────────┼──────────┐
        ↓          ↓          ↓
   CURRICULUM  CONVERSATION  RESEARCH
        │          │          │
   ┌────┴────┐ ┌──┴──┐  ┌────┴────┐
   ↓         ↓ ↓     ↓  ↓         ↓
Concepts  Lectures Terms Users Papers Topics
   │         │    │     │    │         │
Prerequisites  Sections  Co-mention  Citations
   ↓         ↓    ↓     ↓    ↓         ↓
  SAME METRICS: q, TED, continuity, TED_τ
```

### Interpretation Table

| Domain | Node = | Edge = | High q = | High TED = |
|--------|--------|--------|----------|------------|
| **Curriculum** | Concept | Prerequisite | Coherent lesson | Topic shift |
| **Conversation** | Term/Topic | Co-mention | Focused discussion | Subject change |
| **Research** | Paper | Citation | Unified field | Paradigm shift |
| **Code** | Function | Call graph | Modular | Refactoring |
| **Brain** | Region | Connection | Integrated | State change |
| **Organization** | Agent | Communication | Aligned | Restructuring |

---

## VIII. The ZPD-Mid-Distance Correspondence

```
Vygotsky's ZPD (Psychology)
     ↓
   Too Hard ─────┐
                 │
                 │  ← Optimal Learning Zone (ZPD)
                 │
   Too Easy ─────┘
     ↑
Axiom 9: Mid-Distance Optimality

MATHEMATICAL:
∃ r* ∈ D* such that:
  E[gain | distance = r*] ≥ E[gain | distance = r] ∀r

IMPLEMENTATION:
- Conversation: window_size = 6 (not 2, not 50)
- Curriculum: 2-3 prerequisite hops (not 0, not 10)
- Embeddings: Moderate cosine band (not adjacent, not random)

NEUROSCIENCE PARALLEL:
- Brain at edge of chaos (criticality)
- Not too ordered (rigid), not too random (noisy)
- Optimal information processing
```

---

## IX. The Self-Application Loop

```
┌─────────────────────────────────────────┐
│      AXIOMIC AGENT PROJECT              │
│                                         │
│  ┌──────────────────────────────┐      │
│  │  Axioms (Philosophy layer)   │      │
│  └────────┬─────────────────────┘      │
│           ↓                             │
│  ┌──────────────────────────────┐      │
│  │  Implementation (Code layer) │      │
│  └────────┬─────────────────────┘      │
│           ↓                             │
│  ┌──────────────────────────────┐      │
│  │  Analysis (Reporter layer)   │──┐   │
│  └────────┬─────────────────────┘  │   │
│           ↓                         │   │
│  ┌──────────────────────────────┐  │   │
│  │  Metrics: q, TED, continuity │  │   │
│  └────────┬─────────────────────┘  │   │
│           ↓                         │   │
│  ┌──────────────────────────────┐  │   │
│  │  Guidance: improve, extend   │  │   │
│  └────────┬─────────────────────┘  │   │
│           │                         │   │
│           └─────────────────────────┘   │
│               (feedback loop)           │
└─────────────────────────────────────────┘

PROJECT ANALYZES ITSELF:
  q(project) = 0.92 (highly coherent)
  TED(v1→v2) = adding conversation adapter
  continuity(v1,v2) = high (core preserved)

  Resistance:
  R^meas = documentation (good)
  R^model = axioms (complete)
  R^edge = adapter integration (improving)

  Guidance: Validate conversation adapter edges
```

---

## X. The Knowledge Structure Pyramid

```
              UNDERSTANDING
                   △
                  ╱ ╲
                 ╱   ╲
                ╱ TED ╲         ← Path density
               ╱  _τ   ╲
              ╱   ╱ ╲   ╲
             ╱   ╱   ╲   ╲
            ╱___╱     ╲___╲
           ╱   q(e)        ╲    ← Edge quality
          ╱   verification  ╲
         ╱___________________╲
        RELATIONAL EXISTENCE   ← Axiom 5

LEVELS:
1. Base: Everything exists through edges
2. Middle: Edges have quality q(e)
3. Top: Understanding = high-quality paths

EPISTEMOLOGY:
- Knowledge ≠ facts stored
- Knowledge = verified paths through concept graph
- Understanding = TED_τ > threshold
- Gettier cases = low q(e) despite truth
```

---

## XI. The Conversation Dynamics Flow

```
Message Stream
     ↓
┌────────────────────────┐
│ Build Graph (rolling)  │
│ - Extract terms        │
│ - Build co-occurrence  │
│ - Window = last N msgs │
└──────────┬─────────────┘
           ↓
┌────────────────────────┐
│ Compute Signals        │
│ - q (focus)            │
│ - TED (topic drift)    │
│ - continuity (thread)  │
└──────────┬─────────────┘
           ↓
┌────────────────────────┐
│ Classify Step Type     │
│ - stuck                │
│ - deepening            │
│ - exploring            │
│ - scattered            │
│ - pivot                │
└──────────┬─────────────┘
           ↓
┌────────────────────────┐
│ Generate Guidance      │
│ - inject_divergence    │
│ - synthesize_focus     │
│ - acknowledge_bridge   │
│ - continue             │
└──────────┬─────────────┘
           ↓
┌────────────────────────┐
│ Inject into LLM        │
│ - System prompt mod    │
│ - Metacognitive steer  │
└────────────────────────┘
```

---

## XII. The Seven Pillars Mandala

```
                    AXIOMIC
                   SUBSTRATE
                 (Graph + Metrics)
                       |
        ┌──────────────┼──────────────┐
        ↓              ↓              ↓
    COGNITION    NEUROSCIENCE    PHILOSOPHY
   (Schema)    (Connectivity)  (Justification)
        ↓              ↓              ↓
        └──────────────┼──────────────┘
                       ↓
        ┌──────────────┼──────────────┐
        ↓              ↓              ↓
    PSYCHOLOGY      MEMORY           ML
    (Learning)   (Persistence)  (Meta-learning)
        ↓              ↓              ↓
        └──────────────┼──────────────┘
                       ↓
                 INFRASTRUCTURE
                (System Health)

All seven view SAME STRUCTURE:
  q = quality/coherence
  TED = change/drift
  continuity = persistence
  TED_τ = accessibility
```

---

## XIII. The Temporal Evolution View

```
Time →
Step: 0     1     2     3     4     5     6

q:    0.75  0.82  0.87  0.91  0.94  0.89  0.72
      └─────┴─────┴─────┴─────┴─────┴─────┘
            Increasing (converging) ↑    Drop

TED:  0.0   0.25  0.18  0.12  0.08  0.32  0.45
      └─────┴─────┴─────┴─────┴─────┴─────┘
            Decreasing ↓         Spike (pivot!)

cont: 0.0   0.35  0.48  0.58  0.67  0.41  0.28
      └─────┴─────┴─────┴─────┴─────┴─────┘
            Increasing (building) ↑   Drop

INTERPRETATION:
Steps 0-4: Deepening (q↑, TED↓, cont↑)
Step 5: Pivot detected (TED spike, cont drop)
Step 6: New phase begins (q drops, exploring)

ACTION:
- At step 4: Monitor for stuck (q approaching 0.95)
- At step 5: Acknowledge pivot, bridge contexts
- At step 6: Normal exploration resumes
```

---

## XIV. Quick Visual Reference

### Healthy vs Unhealthy States

```
HEALTHY (Optimal Learning)
┌─────────────────────────┐
│ q:    ████████░░ 0.75   │ Good coherence
│ TED:  ███░░░░░░░ 0.28   │ Manageable change
│ cont: █████░░░░░ 0.42   │ Building on prior
│ TED_τ: ████████░ 0.78   │ Well-connected
└─────────────────────────┘

STUCK (Premature Convergence)
┌─────────────────────────┐
│ q:    █████████░ 0.92   │ ⚠ Too coherent
│ TED:  █░░░░░░░░░ 0.09   │ ⚠ Too stable
│ cont: ████████░░ 0.73   │ ⚠ Too repetitive
│ → ACTION: Inject divergence
└─────────────────────────┘

SCATTERED (Lost Coherence)
┌─────────────────────────┐
│ q:    ███░░░░░░░ 0.34   │ ⚠ Too fragmented
│ TED:  ████████░░ 0.76   │ ⚠ Too chaotic
│ cont: ██░░░░░░░░ 0.15   │ ⚠ No connection
│ → ACTION: Synthesize
└─────────────────────────┘
```

---

## XV. The Complete Picture

```
                 AXIOMIC PHILOSOPHY
                    (Relational Monism)
                          |
                  Universal Substrate
                  (Graphs + Metrics)
                          |
        ┌─────────────────┼─────────────────┐
        ↓                 ↓                 ↓
    THEORY            IMPLEMENTATION    APPLICATION
   (Axioms)          (Code/Metrics)   (Domains)
        │                 │                 │
        ├─ Formal         ├─ Pipeline       ├─ Curriculum
        ├─ Complete       ├─ Measurable     ├─ Conversation
        └─ Testable       └─ Debuggable     └─ Research
                          |
                    METACOGNITION
              (Self-application & guidance)
                          |
        ┌─────────────────┼─────────────────┐
        ↓                 ↓                 ↓
  Monitor State    Classify Pattern   Generate Action
  (q,TED,cont)    (stuck/explore...)  (diverge/focus)
```

---

## Conclusion

These maps show that the axiomic framework isn't just theory—it's **operational geometry** of complex systems.

Every discipline is viewing the **same relational structure** through different semantic lenses.

The metrics are **universal invariants** across domains.

The patterns are **recognizable and actionable**.

**The map is the territory when the territory is relational.**

---

## XVI. The Adapter-as-Sensor Architecture

### The 6-Sense Model

**Biological systems:** Multiple sensory modalities → unified neural representation
**AxiomicAgent:** Multiple adapters → unified graph representation

```
EXTERNAL ADAPTERS (Sensory Transduction)
├─ Curriculum Adapter (vision-like)
│  Input: HTML, transcripts, structured content
│  Output: Concept graph (nodes=concepts, edges=prerequisites)
│  Modality: Spatial/structural knowledge
│
├─ Conversation Adapter (hearing-like)
│  Input: Message sequences, dialogue turns
│  Output: Topic graph (nodes=terms, edges=co-mention)
│  Modality: Temporal/sequential information
│
├─ Research Adapter (touch-like)
│  Input: Papers, citations, metadata
│  Output: Knowledge graph (nodes=papers, edges=citations)
│  Modality: Network/relational structure
│
├─ Code Adapter (proprioception-like)
│  Input: Source files, call graphs, dependencies
│  Output: Function graph (nodes=functions, edges=calls)
│  Modality: Executable/causal structure
│
└─ Time-series Adapter (taste/smell-like)
   Input: Events, logs, measurements
   Output: Temporal graph (nodes=states, edges=transitions)
   Modality: Change/drift patterns

INTERNAL ADAPTER (Interoception - The 6th Sense)
└─ Metacognitive Adapter (self-monitoring)
   Input: System state, past signals, resistance
   Output: Self-graph (nodes=components, edges=dependencies)
   Modality: System health, capacity, internal state
```

### ML Grounding: Multimodal Representation Learning

**Key principle:** All modalities project to same latent space

```python
# Standard multimodal ML:
vision_encoder(image) → embedding ∈ ℝ^d
text_encoder(text) → embedding ∈ ℝ^d
audio_encoder(sound) → embedding ∈ ℝ^d

# Axiomic equivalent:
curriculum_adapter(content) → graph(V, E, q)
conversation_adapter(dialogue) → graph(V, E, q)
research_adapter(papers) → graph(V, E, q)

# SAME LATENT STRUCTURE: graph with quality metric
```

**This is Axiom 5 operationalized:**
> Relational Existence: Everything exists through edges; edge quality q(e) ∈ [0,1]

All adapters are **graph encoders**. The shared representation is **not** vectors—it's **relational structure**.

### The Thalamic Core: Universal Graph Processor

```
         ADAPTERS (Encoders)
              |
              ↓
    ┌─────────────────────────┐
    │   CORE ENGINE           │
    │   (Graph Processor)     │
    │                         │
    │   Input: graph(V,E,q)   │
    │   Compute: signals      │
    │     • q (cohesion)      │
    │     • TED (drift)       │
    │     • continuity        │
    │     • TED_τ             │
    │   Output: Signals       │
    └──────────┬──────────────┘
               ↓
    ┌─────────────────────────┐
    │   REPORTERS (Decoders)  │
    │                         │
    │   Signal → Guidance     │
    │   Signal → Insights     │
    │   Signal → Dynamics     │
    └─────────────────────────┘
```

**ML equivalent:** Encoder-processor-decoder architecture

```python
# Vision transformer:
patch_embed → transformer_blocks → classification_head

# AxiomicAgent:
adapter → core_engine → reporters
```

---

## XVII. Capacity Dynamics & System States

### Axiom 2 Extended: Computational Budget as Thermodynamics

**From Axiom 2 (Capacity Budgeting):**
```
∑ cost(x_t → x_{t+1}) ≤ ∑ C_t
```

**Extended to system states:**

```python
# System state = f(capacity, resistance, drift)

capacity_state = {
    "available": C_t,           # Unused compute budget
    "consumed": ∑ cost(x),      # Used resources
    "surplus": C_t - ∑ cost(x)  # Free capacity
}

resistance_state = {
    "measurement": R^meas,      # Data quality bottleneck
    "model": R^model,           # Representation mismatch
    "edge": R^edge,             # Connectivity friction
    "total": R^meas + R^model + R^edge
}

drift_state = {
    "current_TED": TED_t,       # Change magnitude
    "available_TED": max_TED - TED_t,  # Remaining exploration
}
```

### The Capacity-Resistance Phase Diagram

```
         HIGH CAPACITY SURPLUS
              ↑
              |
   UNDER-     |  READY
   UTILIZED   |  (High C, Low R,
   (Bored)    |   can handle ↑TED)
              |
    ─ ─ ─ ─ ─ + ─ ─ ─ ─ ─ → HIGH RESISTANCE
              |
   OPTIMAL    |  SATURATED
   (Flow)     |  (Low C, High R,
   C ≈ R      |   need ↓TED or ↑C)
              |
         LOW CAPACITY SURPLUS
```

### ML Interpretation Table

| System State | Capacity | Resistance | TED | ML Analog | Intervention |
|--------------|----------|------------|-----|-----------|--------------|
| **Under-utilized** | High | Low | Low | Model too simple, data too easy | ↑ Model complexity, ↑ Task difficulty |
| **Optimal (Flow)** | Medium | Medium | Medium | Good train regime | Continue |
| **Ready** | High | Low | Med-High | Can handle harder data | ↑ Curriculum difficulty |
| **Saturated** | Low | High | High | Overfitting, not converging | ↓ Learning rate, ↓ Batch complexity |
| **Exploring** | Medium | Medium | Med-High | Active learning zone | Sample at mid-distance |
| **Stuck** | Medium | Low | Very Low | Converged prematurely | Inject noise, perturb parameters |

### Boredom = Free Capacity (Potential Energy)

**Thermodynamic view:**
```
Free energy F = U - TS
(Available energy = Total energy - Entropy penalty)

Axiomic equivalent:
Free capacity = C_available - R_current

When Free_capacity >> 0:
  System is "bored" (underutilized)
  Potential energy stored
  Ready for harder tasks
```

**ML grounding:**

```python
# Training dynamics:
class SystemState:
    def __init__(self, capacity, resistance):
        self.C = capacity           # Compute budget (FLOPs, memory)
        self.R = resistance         # Problem difficulty

    def free_capacity(self):
        return self.C - self.R

    def state_classification(self):
        free = self.free_capacity()

        if free > 0.5 * self.C:
            # Massive surplus
            return "underutilized"  # "Bored"
            # Signal: Can handle 2x harder problems

        elif -0.1 * self.C < free < 0.1 * self.C:
            # Balanced
            return "optimal"  # "Flow"
            # Signal: Continue current regime

        else:
            # Deficit
            return "saturated"  # "Overwhelmed"
            # Signal: Reduce difficulty or increase capacity
```

**NOT anthropomorphizing—this is resource allocation:**

- Boredom ≡ Compute budget underutilized
- Flow ≡ Resources matched to task
- Overwhelm ≡ Task exceeds available compute

### Curriculum Learning via Capacity Matching

**Bengio et al. (2009): Start easy, increase difficulty**

**Axiomic formulation:**

```python
def adaptive_curriculum(learner, task_pool):
    """
    Match task difficulty to learner capacity
    Maximize learning rate without saturation
    """
    C_t = learner.available_capacity()

    # Find tasks where R ≈ 0.7 * C_t
    # (Leave 30% margin for variance)
    target_resistance = 0.7 * C_t

    tasks = [
        t for t in task_pool
        if abs(t.resistance - target_resistance) < threshold
    ]

    # Among matched tasks, select mid-distance from current
    current_state = learner.get_state()
    best_task = select_mid_distance(tasks, current_state)

    return best_task
```

**This operationalizes:**
- Axiom 2 (Capacity matching)
- Axiom 9 (Mid-distance optimality)

### The Interoceptive Signal: Resistance Decomposition

**ML equivalent:** Loss decomposition for debugging

```python
# Standard ML loss:
total_loss = cross_entropy(pred, target)
# → Black box, hard to debug

# Axiomic resistance:
R_total = R_meas + R_model + R_edge
# → Each component has clear intervention

R_meas = measurement_noise / signal_strength
  # Intervention: Better data collection, preprocessing
  # ML: Clean dataset, fix labels, augment

R_model = representation_mismatch
  # Intervention: Change architecture, change features
  # ML: Different model family, feature engineering

R_edge = 1 - TED_τ
  # Intervention: Build connections, improve flow
  # ML: Better curriculum order, transfer learning
```

**This is introspection without anthropomorphism:**

```python
class MetacognitiveMonitor:
    """The 6th sense: System monitoring itself"""

    def compute_internal_state(self):
        """Compute system health metrics"""
        return {
            # Capacity monitoring:
            "capacity_used": self.compute_utilization(),
            "capacity_free": self.compute_surplus(),

            # Resistance monitoring:
            "R_meas": self.diagnose_data_quality(),
            "R_model": self.diagnose_representation(),
            "R_edge": self.diagnose_connectivity(),

            # State classification:
            "learning_rate": self.estimate_progress(),
            "regime": self.classify_regime(),  # stuck/exploring/optimal
        }

    def generate_guidance(self, internal_state):
        """Map internal state → intervention"""
        if internal_state["regime"] == "underutilized":
            return "increase_task_difficulty"
        elif internal_state["regime"] == "saturated":
            return "decrease_task_difficulty"
        elif internal_state["regime"] == "stuck":
            return "inject_exploration"
        else:
            return "continue"
```

### Energy State Transitions (ML Grounding)

```
TRAINING DYNAMICS:

Start: Random init
  → High R (hard to fit), High C (full budget)
  → State: Saturated

Early training:
  → R decreasing (fitting training set)
  → C matched to R
  → State: Optimal flow

Convergence:
  → R → 0 (train loss → 0)
  → C surplus increasing
  → State: Underutilized ("bored")
  → Signal: Need harder task or regularization

Overfitting:
  → R_train → 0, R_val high
  → State: Stuck in local minimum
  → Signal: Inject exploration (dropout, augmentation)
```

**The "boredom" signal in ML:**

```python
if train_loss < threshold and capacity_surplus > 0.5:
    # Model has "excess capacity"
    # Options:
    # 1. Increase model capacity (wider/deeper)
    # 2. Increase task difficulty (harder data)
    # 3. Multi-task learning (deploy surplus elsewhere)

    # This is EXACTLY "boredom as potential energy"
    # System signaling: "I can do more"
```

### Active Learning & Exploration

**When to explore (increase TED):**

```python
def should_explore(state):
    """
    Exploration is productive when:
    - Capacity available (C > R)
    - Current TED low (stuck)
    - Potential for mid-distance gains
    """
    if state.free_capacity() > threshold:
        if state.TED < 0.15:  # Stuck
            # High capacity, low drift → BORED
            # Inject exploration
            return True, "sample_mid_distance"
        elif state.TED > 0.5:  # Too much change
            # Need consolidation
            return False, "exploit_current"
    else:
        # Capacity exhausted
        return False, "reduce_load"
```

**ML implementation:**

```python
# Exploration-exploitation via capacity
if model.has_free_capacity() and data.is_repetitive():
    # Underutilized + low TED = "bored"
    # Action: Sample harder examples
    next_batch = active_learning_query(
        pool=unlabeled_data,
        strategy="mid_distance",  # Axiom 9
        distance_metric=embedding_distance,
        current_state=model.state
    )
else:
    # Optimal or saturated
    # Action: Continue current regime
    next_batch = standard_sampling(train_data)
```

---

## XVIII. Cross-Domain Capacity Metrics

### Universal Capacity Table

| Domain | Capacity (C) | Resistance (R) | Free Energy | Intervention |
|--------|--------------|----------------|-------------|--------------|
| **ML Training** | FLOPs, memory, time | Loss, gradient norm | Unused compute | ↑ Model size or ↑ data difficulty |
| **Curriculum** | Student bandwidth | Content difficulty | Attention surplus | ↑ Material complexity |
| **Conversation** | Context window | Topic complexity | Unused tokens | ↑ Depth or ↑ breadth |
| **Research** | Researcher time | Problem hardness | Unallocated hours | ↑ Ambition or ↓ scope |
| **Code** | CPU/memory | Algorithm complexity | Idle cycles | ↑ Workload or optimize |
| **Neural** | Synapses, energy | Task demand | Available neurons | ↑ Task difficulty |

### The Universal Pattern

**Across all domains:**

```python
optimal_state = {
    "capacity_utilization": 0.7,  # 70% used, 30% margin
    "TED": in_mid_distance_band,  # Not stuck, not chaotic
    "continuity": 0.2 - 0.5,      # Building on prior
    "resistance": matched_to_capacity,
}

underutilized_state = {
    "capacity_utilization": 0.3,  # 70% FREE
    "TED": very_low,              # Repetitive
    "signal": "bored/ready",
    "action": "increase_difficulty",
}

saturated_state = {
    "capacity_utilization": 0.95, # 95% used, no margin
    "TED": very_high,             # Overwhelming
    "signal": "overwhelmed",
    "action": "decrease_difficulty",
}
```

---

## XIX. Implementation: Capacity-Aware Guidance

### Metacognitive Monitoring (ML-Grounded)

```python
class CapacityAwareAgent:
    """
    Agent that monitors its own capacity/resistance dynamics
    Adjusts exploration based on available resources
    """

    def __init__(self, capacity_budget):
        self.C_max = capacity_budget
        self.C_available = capacity_budget
        self.history = []

    def process_step(self, graph_t, graph_prev):
        """Process one step and update state"""

        # Compute signals (Axiom 5)
        signals = compute_signals(graph_t, graph_prev)

        # Measure resistance (Axiom 8)
        R = self.measure_resistance(signals)

        # Compute free capacity
        cost = self.step_cost(graph_t)
        self.C_available -= cost
        free_capacity = self.C_available

        # Classify state
        state = self.classify_state(
            free_capacity, R, signals.TED
        )

        # Generate guidance
        guidance = self.generate_guidance(state, signals)

        return guidance

    def classify_state(self, C_free, R, TED):
        """Map (C, R, TED) → system state"""

        util = 1 - (C_free / self.C_max)

        if util < 0.4:
            if TED < 0.15:
                return "underutilized"  # Bored
            else:
                return "ready"  # Ready for hard task
        elif 0.4 <= util <= 0.8:
            if 0.2 < TED < 0.4:
                return "optimal"  # Flow
            elif TED < 0.15:
                return "stuck"  # Converged
            else:
                return "exploring"  # Learning
        else:  # util > 0.8
            return "saturated"  # Overwhelmed

    def generate_guidance(self, state, signals):
        """State → intervention"""

        guidance_map = {
            "underutilized": {
                "action": "increase_difficulty",
                "reason": "Capacity surplus, low change",
                "intervention": "sample_harder_examples",
            },
            "ready": {
                "action": "accept_challenge",
                "reason": "Capacity available, moderate change",
                "intervention": "continue_with_margin",
            },
            "optimal": {
                "action": "continue",
                "reason": "Balanced capacity/resistance",
                "intervention": "maintain_regime",
            },
            "stuck": {
                "action": "inject_exploration",
                "reason": "Low change despite capacity",
                "intervention": "sample_mid_distance",
            },
            "exploring": {
                "action": "continue",
                "reason": "Learning in progress",
                "intervention": "monitor_for_saturation",
            },
            "saturated": {
                "action": "reduce_difficulty",
                "reason": "Capacity exhausted",
                "intervention": "simplify_or_rest",
            },
        }

        return guidance_map[state]

    def measure_resistance(self, signals):
        """Decompose resistance (Axiom 8)"""

        # Measurement resistance: data quality
        R_meas = self.estimate_noise_level()

        # Model resistance: representation quality
        R_model = 1 - signals.q  # Low cohesion = high resistance

        # Edge resistance: connectivity
        R_edge = 1 - signals.TED_tau

        return {
            "meas": R_meas,
            "model": R_model,
            "edge": R_edge,
            "total": R_meas + R_model + R_edge,
        }
```

### Example Usage: Adaptive Curriculum

```python
# Initialize agent with compute budget
agent = CapacityAwareAgent(capacity_budget=1000)

# Process curriculum steps
for step_t in curriculum:
    graph_t = adapter.process(step_t)
    graph_prev = adapter.get_previous()

    guidance = agent.process_step(graph_t, graph_prev)

    if guidance["action"] == "increase_difficulty":
        # Student is "bored" (underutilized)
        # Jump ahead or add enrichment
        print(f"Step {step_t.id}: Surplus capacity detected")
        print(f"  → Add challenge problems")

    elif guidance["action"] == "reduce_difficulty":
        # Student is saturated
        # Slow down or review
        print(f"Step {step_t.id}: Capacity exhausted")
        print(f"  → Review previous material")

    elif guidance["action"] == "inject_exploration":
        # Student is stuck
        # Add mid-distance examples
        print(f"Step {step_t.id}: Convergence detected")
        print(f"  → Introduce related topic")
```

---

## Conclusion (Updated)

These maps demonstrate that the axiomic framework provides:

1. **Universal substrate**: Graphs + metrics work across all domains
2. **Capacity dynamics**: System states as resource allocation, not subjective feelings
3. **Multimodal encoding**: Adapters as graph encoders to shared representation space
4. **Introspective monitoring**: The 6th sense as self-measurement without anthropomorphism
5. **Operational guidance**: State classification → intervention mapping

**The framework is ML-native:**
- Boredom = underutilization (potential energy)
- Flow = optimal resource allocation
- Overwhelm = saturation (capacity exhausted)
- Exploration = mid-distance sampling (Axiom 9)
- Resistance = debuggable bottleneck (Axiom 8)

**Every "emotional" state has a computational equivalent.** The axioms reveal universal patterns in resource-constrained optimization, whether implemented in neural tissue or silicon.

---

*For interactive versions of these diagrams, see the visualization tools in development.*

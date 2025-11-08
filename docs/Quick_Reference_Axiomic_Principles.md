# Quick Reference: Axiomic Principles in Practice

**One-Page Guide for Applying the Axioms**

---

## Core Principle

> **Everything exists through relationships. Quality = edge quality.**

---

## The Seven Universal Metrics

| Metric | What It Measures | When to Use | Interpretation |
|--------|-----------------|-------------|----------------|
| **q** | Coherence/cohesion within a unit | Every step | 0.7-0.9 = healthy, >0.9 = converging, <0.5 = scattered |
| **TED** | Drift/change between units | Step transitions | 0.15-0.35 = learning, <0.15 = stagnant, >0.5 = pivot |
| **continuity** | Overlap/persistence | Memory/retention | 0.2-0.5 = balanced, >0.6 = repetitive, <0.2 = novel |
| **spread** | Distribution/connectivity | System health | 0.3-0.6 = balanced integration/segregation |
| **TED_τ** | Verified path density | Knowledge access | >0.7 = well-connected, <0.3 = isolated |
| **phases** | Regime boundaries | Structure detection | Count major TED spikes |
| **resistance** | Friction sources | Debugging | R^meas + R^model + R^edge |

---

## The 10 Axioms (One-Liners)

1. **Typed Bounds**: Rules come in three types—immutable, editable-with-cost, preference
2. **Capacity**: Everything consumes finite budget
3. **Tariffs**: Changes have costs proportional to impact
4. **Commit**: Mode changes have inertia and reversal penalties
5. **Relational Existence**: Things exist through edges; edge quality determines everything
6. **Handoff Contracts**: Layer boundaries need explicit specifications
7. **Order**: History matters; you can't costlessly undo
8. **Resistance = Measurement + Model + Edge**: Problems decompose cleanly
9. **Mid-Distance Optimality**: Best exploration at intermediate scales
10. **Recursive Composition**: Systems compose from verified subsystems

---

## Pattern Recognition

### Healthy System
- q: 0.7-0.9 (coherent but not rigid)
- TED: 0.15-0.35 (changing but not chaotic)
- continuity: 0.2-0.5 (building on prior but adding new)
- TED_τ: >0.7 (well-connected)

### Stuck/Converging
- q: >0.85 (too tight)
- TED: <0.15 (stagnant)
- continuity: >0.5 (repeating)
- **Action**: Inject divergence (explore alternatives)

### Scattered/Lost
- q: <0.5 (fragmented)
- TED: >0.5 (chaotic)
- continuity: <0.2 (disconnected)
- **Action**: Synthesize (find common threads)

### Pivoting
- TED: >0.5 (major shift)
- continuity: 0.2-0.4 (some connection)
- **Action**: Acknowledge transition, bridge contexts

---

## Intervention Guide

### When to Act

```
IF stuck (high q, low TED, high continuity):
    → Inject divergence
    → Sample at mid-distance from current focus
    → Ask "what if?" questions

IF scattered (low q, high TED, low continuity):
    → Synthesize and focus
    → Identify common threads
    → Build bridging connections

IF optimal (balanced metrics):
    → Continue current approach
    → Monitor for drift

IF pivoting (high TED):
    → Acknowledge the shift
    → Connect to prior context
    → Prepare for new phase
```

### Resistance Triage

```
IF problem persists:
    Measure R^meas (data quality)
    Measure R^model (representation quality)
    Measure R^edge (connectivity quality)

    Fix dominant component:
    - R^meas → Better sensors/instruments
    - R^model → Change closure/split regime
    - R^edge → Build connections/raise TED_τ
```

---

## Domain Translation Table

| You Call It | We Call It | Metric |
|------------|-----------|--------|
| Understanding | TED_τ (path density) | >0.7 |
| Learning | TED (graph change) | 0.15-0.35 |
| Memory | continuity (persistence) | 0.2-0.5 |
| Confusion | Low q + high TED | Both poor |
| Mastery | High q + low TED | Both good |
| Insight | TED spike + q increase | Step change |
| Forgetting | Continuity drop | <0.2 |
| Integration | Low spread | <0.3 |
| Creativity | Mid-distance sampling | Axiom 9 |

---

## Practical Workflows

### Analyzing a Curriculum

```python
1. Build graph from materials
2. Compute q, TED, continuity per step
3. Identify pivots (high TED)
4. Check balance (q vs TED tradeoff)
5. Optimize order (minimize total TED while covering content)
```

### Steering a Conversation

```python
1. Track last N messages as graph
2. Compute current q, TED, continuity
3. Classify: stuck | deepening | exploring | scattered | pivot
4. Generate guidance modifier for LLM
5. Update graph with new message
```

### Debugging a System

```python
1. Identify stalled progress
2. Decompose: R^meas | R^model | R^edge
3. Target dominant resistance:
   - Measurement → Upgrade sensors
   - Model → Change representation
   - Edge → Build connections
4. Measure improvement via TED_τ increase
```

---

## Key Equations

### Core Signals
```
q = cohesion(edges_within_step)
TED = 1 - |current ∩ previous| / |current ∪ previous|
continuity = |current_nodes ∩ previous_nodes| / |current_nodes ∪ previous_nodes|
```

### Edge Quality
```
q(e) = α·verification + β·authority + γ·recency + δ·locality
where α + β + γ + δ = 1
```

### Understanding
```
Understanding(X,Y) = g(Edges(X ↔ Y))
Knowledge(X) = TED_τ(axioms → X) where all q(e) > τ
```

### Resistance
```
R_total = R^meas + R^model + R^edge
R^meas ∝ noise/signal
R^model ∝ residual structure
R^edge = 1 - TED_τ
```

---

## Common Mistakes

❌ **Optimizing q alone** → Premature convergence
✅ **Balance q and TED** → Healthy learning

❌ **Ignoring continuity** → Forgetting/discontinuity
✅ **Monitor continuity** → Spaced reinforcement

❌ **Random exploration** → Inefficient search
✅ **Mid-distance sampling** → Optimal discovery

❌ **Treating symptoms** → Temporary fixes
✅ **Decompose resistance** → Target root cause

❌ **Implicit assumptions** → Paradoxes arise
✅ **Explicit contracts** → Clean handoffs

---

## Quick Diagnostics

**Is my curriculum well-designed?**
- Avg q: 0.7-0.9 ✓
- Avg TED: 0.1-0.25 ✓
- Pivots align with intended units ✓
- High continuity for core concepts ✓

**Is my conversation productive?**
- q: 0.5-0.8 (focused but flexible) ✓
- TED: 0.2-0.4 (evolving but coherent) ✓
- Not stuck (q < 0.85, TED > 0.15) ✓
- Not scattered (q > 0.4, TED < 0.6) ✓

**Is my system healthy?**
- TED_τ: >0.6 (well-connected) ✓
- Spread: 0.3-0.6 (balanced) ✓
- Resistance decomposed and improving ✓
- Clear handoff contracts ✓

---

## One-Sentence Summary

**The axioms reveal that all complex systems—brains, curricula, conversations, organizations—are graphs whose behavior is determined by edge quality, and optimal dynamics live at mid-distance between order and chaos.**

---

## Further Reading

- Full analysis: `docs/Axiomic_Cross_Disciplinary_Analysis.md`
- Formal axioms: `Philosophy/Axioms_v2_Operational.tex`
- Implementation: `docs/PIPELINE.md`
- Case studies: `Philosophy/Axioms_v2_Case_Studies_Examples.tex`

---

*When in doubt: Measure q and TED, decompose resistance, act on dominant component.*

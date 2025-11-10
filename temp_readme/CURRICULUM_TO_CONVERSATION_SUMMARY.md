# From Curriculum Analysis to Conversation Design: Summary

## The Bridge: How Learning Theory Informs AI Communication

This document summarizes how insights from curriculum analysis (effective teaching content) translate into conversation health monitoring (effective AI communication).

---

## Key Curriculum Findings

From analyzing 17 educational curricula:

### High-Quality Teaching Patterns (q > 0.90)

| Course | Quality | Drift | Steps | Key Pattern |
|--------|---------|-------|-------|-------------|
| **Chemistry 5.111sc** | 0.963 | 0.074 | 50 | Highest quality: Chunked, verified, structured |
| **MIT Calculus 18.01** | 0.916 | 0.024 | 204 | Progressive revelation: Each concept builds on previous |
| **Biology 7.01sc** | 0.930 | 0.095 | 34 | Mixed regimes: Deep focus + transitions |
| **Psychology 9.00sc** | 0.948 | 0.083 | 30 | Spiral learning: Revisit at deeper levels |

### Core Insights

1. **Progressive Revelation**: Start simple, verify understanding, advance deeper (q=0.916, drift=0.024)
2. **Chunking**: Break complex topics into 30-50 digestible steps while maintaining coherence
3. **Verification**: High-quality curricula include frequent understanding checks
4. **Dependencies**: Respect prerequisites (can't teach derivatives before limits)
5. **Spiral Structure**: Introduce → revisit deeper → master

---

## Mapping to Conversation Contexts

### Before (Generic Context Classification)

```
TEACHING Context:
  - Signals: "how does", "explain"
  - Max drift: 0.50
  - Action: Clear explanation with examples
```

### After (Curriculum-Informed)

```
TEACHING Context (Curriculum-Informed):

Learning Phase Detection:
  - Introduction: User exploring ("what is") → drift < 0.50
  - Deep Dive: User focusing ("how does") → drift < 0.20 (MIT math pattern)
  - Transition: User connecting ("how relates") → drift < 0.60
  - Review: User summarizing ("recap") → drift < 0.40

Progressive Revelation:
  - Start with foundation (like MIT 18.01)
  - Check understanding every 3-5 concepts (like high-quality curricula)
  - Advance only after verification

Chunking:
  - Max 3 concepts per turn (cognitive load management)
  - Break long explanations like curricula break into 30-50 steps

Concept Dependencies:
  - Track prerequisites
  - Don't explain backpropagation before gradient descent
  - Like curriculum: can't teach calculus without algebra

Spiral Deepening:
  - First mention: Surface level
  - After 5-10 concepts: Revisit deeper
  - After mastery: Connect to advanced topics

Verification Loops:
  - Check every 5-6 turns (high-quality curriculum pattern)
  - "Does this make sense before we continue?"
```

---

## Concrete Examples

### Example 1: Teaching Neural Networks

**Before (No Curriculum Awareness)**:

```
User: "How do neural networks work?"
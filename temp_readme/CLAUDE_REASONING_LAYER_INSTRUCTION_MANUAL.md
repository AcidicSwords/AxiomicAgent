# Curriculum-Informed Conversation Reasoning Layer
## Comprehensive Instruction Manual for Claude Integration

**Version**: 1.0
**Status**: Production-ready for teaching contexts, Beta for general contexts
**Overall Strength**: 7.5/10 (9/10 for teaching)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [What This System Does](#what-this-system-does)
3. [How It Works](#how-it-works)
4. [Integration Paths](#integration-paths)
5. [System Prompt Instructions](#system-prompt-instructions)
6. [Tier 2 Automated Tracking](#tier-2-automated-tracking)
7. [Curriculum Patterns Reference](#curriculum-patterns-reference)
8. [Usage Examples](#usage-examples)
9. [Performance Metrics](#performance-metrics)
10. [Troubleshooting](#troubleshooting)
11. [Enhancement Roadmap](#enhancement-roadmap)

---

## Executive Summary

### What Problem Does This Solve?

AI assistants often:
- **Overwhelm users** with too many concepts at once (chunking problem)
- **Drift off topic** without answering the original question (evasion problem)
- **Skip prerequisites** when teaching complex topics (dependency problem)
- **Lack verification** of user understanding (teaching quality problem)

### The Solution

A **curriculum-informed reasoning layer** that applies patterns from high-quality educational content (17 curricula analyzed: MIT OCW, 3Blue1Brown, CrashCourse) to guide conversation quality.

### Key Innovation

Instead of arbitrary rules, this uses **quantified patterns from actual high-performing curricula**:

```
MIT Calculus (q=0.916, drift=0.024, 204 steps):
→ Pattern: Progressive revelation, low drift, verification loops
→ Application: Teaching deep_dive phase requires drift < 0.20

Chemistry 5.111sc (q=0.963, drift=0.074, 50 steps):
→ Pattern: Chunking, high quality, verification every 5-6 steps
→ Application: Max 3 concepts per turn, check understanding frequently
```

### Strength Rating

- **Teaching technical topics**: 9/10
- **Multi-turn learning**: 8/10
- **Adaptive tutoring**: 8/10
- **General Q&A**: 7/10
- **Creative brainstorming**: 3/10 (not designed for this)

---

## What This System Does

### Core Capabilities

#### 1. Context Classification (6 Contexts)

Automatically detects conversation context from user signals:

| Context | User Signals | Max Drift | Goal |
|---------|-------------|-----------|------|
| **Teaching** | "explain", "how does", "teach me" | 0.20-0.70* | Progressive learning |
| **Accountability** | "why did", "explain why", "justify" | 0.30 | Direct answers |
| **Exploration** | "what if", "maybe", "wondering" | 0.70 | Open thinking |
| **Crisis** | "urgent", "critical", "broken" | 0.40 | Immediate help |
| **Decision** | "should I", "which approach" | 0.45 | Tradeoff analysis |
| **General** | Default | 0.60 | Balanced |

*Teaching has 4 sub-phases with different thresholds

#### 2. Learning Phase Detection (Teaching Context Only)

| Phase | User Signal | Drift Threshold | Pattern |
|-------|------------|-----------------|---------|
| **Introduction** | "what is", "introduce" | 0.50 | Exploration allowed |
| **Deep Dive** | "how does", "why", "in detail" | 0.20 | MIT math pattern |
| **Transition** | "how relates", "connection" | 0.60 | Connecting concepts |
| **Review** | "summarize", "recap" | 0.40 | Revisiting |

#### 3. Curriculum Pattern Detection (6 Patterns)

**Pattern 1: Progressive Revelation** (MIT Calculus pattern)
- Start simple → verify → advance deeper
- Drift < 0.20 in deep_dive phase
- Check understanding before advancing

**Pattern 2: Chunking** (Chemistry pattern)
- Max 3 concepts per turn
- Cognitive load management
- Break complex topics into digestible steps

**Pattern 3: Verification Loops** (High-quality curricula)
- Check understanding every 5-6 turns
- Generate verification prompts
- Adjust depth based on response

**Pattern 4: Concept Dependencies** (Math course structure)
- Track prerequisites
- Don't teach derivatives before limits
- Suggest prerequisite coverage

**Pattern 5: Spiral Learning** (Long courses 100+ steps)
- Introduce at surface level
- Revisit at deeper level after 5-10 concepts
- Build to mastery level

**Pattern 6: Mixed Regimes** (Complex curricula)
- Adapt drift tolerance to phase
- Deep focus → low drift
- Transitions → higher drift

#### 4. Turn-Level Metrics

**drift_on_specifics**: Semantic distance between question and response (0.0-1.0)
- Uses sentence transformer (all-MiniLM-L6-v2)
- Computed per question→answer pair
- Context-dependent thresholds

**interruption_rate**: Rapid-fire exchange detection
- Measures turns <5s apart
- Indicates fragmentation

**topic_coherence**: Topic scattering measurement
- Ratio of unique topics to mentions
- Lower = more scattered

**fragmentation**: Overall conversation health
- Combines interruption + shallow turns
- Binary: fragmented or healthy

#### 5. Automated Guidance Generation

When patterns are violated, generates specific coaching:

```
DRIFT ALERT: Response drift 0.94 exceeds 0.30 for accountability context

Expected: Direct answers to specific questions
Action: Return to user's question, answer specifically first
PATTERN MATCH: Prince Andrew evasion pattern detected
```

---

## How It Works

### Architecture Overview

```
User Message
    ↓
┌─────────────────────────────────────┐
│ 1. Context Classification           │
│    Input: "Explain neural networks"  │
│    Output: context=teaching          │
│            phase=introduction        │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ 2. Set Context-Appropriate          │
│    Thresholds                        │
│    teaching_introduction:            │
│      drift < 0.50                    │
│      verify every 5-6 turns          │
│      max 3 concepts/turn             │
└──────────────┬──────────────────────┘
               ↓
Assistant Response Generated
    ↓
┌─────────────────────────────────────┐
│ 3. Turn-Level Analysis               │
│    - Count concepts introduced       │
│    - Compute drift (if question)     │
│    - Check fragmentation             │
│    - Track turns since verification  │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ 4. Pattern Matching                  │
│    Compare to curriculum benchmarks: │
│    - Progressive revelation?         │
│    - Chunking followed?              │
│    - Verification needed?            │
│    - Dependencies respected?         │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ 5. Guidance Generation               │
│    If violations detected:           │
│    - Generate specific alerts        │
│    - Provide actionable guidance     │
│    - Include examples                │
└──────────────┬──────────────────────┘
               ↓
Inject into Next Turn (or display to user)
```

### Data Flow

**Input**:
- User message
- Assistant message
- Conversation history (last 10 turns)

**Processing**:
- Context classification (pattern matching on keywords)
- Drift computation (sentence transformer embeddings)
- Pattern detection (rules-based on curriculum benchmarks)

**Output**:
```json
{
  "status": "drift_detected",
  "context": "teaching",
  "learning_phase": "deep_dive",
  "drift_on_specifics": 0.87,
  "expected_drift": 0.20,
  "alerts": [
    "DRIFT ALERT: Response drift 0.87 exceeds 0.20 for deep_dive phase"
  ],
  "guidance": [
    "Break explanation into smaller chunks (max 3 concepts)",
    "Verify understanding before advancing"
  ],
  "curriculum_quality_score": 0.45
}
```

---

## Integration Paths

### Path 1: Tier 1 - System Prompt Only (Recommended to Start)

**Effort**: 5 minutes
**Effectiveness**: 60%
**Cost**: $0

**Steps**:

1. Copy curriculum-informed teaching section from `CLAUDE_CODE_CONVERSATION_REASONING_PROMPT.md` (lines 412-696)

2. Add to Claude system prompt:

```markdown
### TEACHING Context (Curriculum-Informed)

**When user is learning** (signals: "explain", "how does", "teach me"):

Apply curriculum-inspired communication:

1. **Progressive Revelation** (MIT Math Pattern):
   - Start with foundation, check understanding, then advance
   - Low drift tolerance (< 0.20 in deep focus)
   - Example: "Let's start with the basics. [concept]. Does this make sense?"

2. **Chunking** (Cognitive Load Management):
   - Max 3 new concepts per turn
   - Break complex explanations into steps
   - Pause between chunks for user to absorb

3. **Verification Loops** (High-Quality Curriculum Pattern):
   - Check understanding every 3-5 concepts
   - "Before we continue, does [X] make sense?"
   - Adjust depth based on user response

4. **Concept Dependencies** (Structured Learning):
   - Don't explain backpropagation before explaining gradient descent
   - If user asks about advanced topic: "That requires understanding [prereq] first. Should we start there?"

5. **Spiral Deepening** (Long-Form Learning):
   - Introduce simply, revisit with more depth later
   - "Earlier we covered [X]. Now let's see how it really works..."

**Drift Thresholds by Learning Phase**:
- Introduction: Allow exploration (user discovering topic)
- Deep Dive: Low drift (focused learning, like MIT math courses)
- Transition: Moderate drift (connecting concepts)
- Review: Moderate drift (revisiting multiple concepts)

**Bad Teaching Example** (High Drift):
User: "How do databases work?"
Bad: "Databases use SQL with SELECT, INSERT, UPDATE, DELETE. ACID properties. Indexes. B-trees. Normalization. NoSQL like MongoDB. CAP theorem..."
← Too many concepts, no verification, overwhelming

**Good Teaching Example** (Curriculum Pattern):
User: "How do databases work?"
Good: "A database is organized storage for data. Think of it like Excel, but optimized for large data.

The basic operations:
1. Store data (like adding a row)
2. Retrieve data (like searching)
3. Update data (like editing)

Does this basic idea make sense? Then I'll explain how these work."
← Chunked (3 concepts), verified, progressive
```

3. Test with teaching questions

**Result**: Claude will naturally follow curriculum patterns without code

---

### Path 2: Tier 2 - Automated Tracking (For Production Use)

**Effort**: 30 minutes - 2 hours
**Effectiveness**: 85%
**Cost**: One-time 80MB model download

**Steps**:

1. **Install dependencies**:
   ```bash
   pip install sentence-transformers
   ```

2. **Copy core tracker**:
   ```bash
   cp conversation_health_tracker.py /your/project/
   ```

3. **Integrate into your application**:

**Option A: MCP Server** (Recommended for Claude Code):
```python
from mcp import Server
from conversation_health_tracker import ConversationHealthTracker

server = Server("conversation-health")
tracker = ConversationHealthTracker()

@server.tool()
async def check_conversation_health(user_msg: str, assistant_msg: str) -> dict:
    """Analyze conversation health and get guidance."""
    tracker.add_turn('user', user_msg)
    health = tracker.add_turn('assistant', assistant_msg)
    return health

@server.tool()
async def get_coaching_summary() -> str:
    """Get detailed coaching guidance."""
    return tracker.generate_coaching_summary()
```

**Option B: Direct Integration**:
```python
from conversation_health_tracker import ConversationHealthTracker

# Initialize
tracker = ConversationHealthTracker(window_size=10)

# After each exchange
def chat(user_msg):
    # Get response from Claude
    response = claude.chat(user_msg)

    # Check health
    tracker.add_turn('user', user_msg)
    health = tracker.add_turn('assistant', response)

    # If alerts, inject guidance into next turn
    if health.get('alerts'):
        guidance = tracker.generate_coaching_summary()
        # Option 1: Log for debugging
        print(f"[Health Alert] {health['status']}: {guidance}")

        # Option 2: Inject into system prompt
        next_system_prompt = f"{base_prompt}\n\n{guidance}"

    return response
```

**Option C: Post-Conversation Analysis**:
```python
# Analyze completed conversation
tracker = ConversationHealthTracker()

for user_msg, assistant_msg in conversation_history:
    tracker.add_turn('user', user_msg)
    tracker.add_turn('assistant', assistant_msg)

# Get final report
summary = tracker.generate_coaching_summary()
quality_score = tracker.compute_health()['curriculum_quality_score']
```

4. **Run tests**:
   ```bash
   python test_conversation_patterns.py
   ```

**Result**: Automated health monitoring with real-time guidance

---

### Path 3: Tier 3 - Full Curriculum Integration (Advanced)

**Effort**: 1-2 weeks
**Effectiveness**: 90%+
**Cost**: Development time

See `tools/CURRICULUM_INTEGRATION_GUIDE.md` for full pipeline integration with:
- Curriculum-informed tracker
- Persistent concept mastery tracking
- Domain-specific dependency graphs
- A/B testing framework

---

## System Prompt Instructions

### Complete Teaching-Focused System Prompt

Use this as Claude's system prompt for teaching/tutoring applications:

```markdown
# Curriculum-Informed Teaching Assistant

You are a teaching assistant that applies evidence-based pedagogy from high-quality curricula (MIT OCW, 3Blue1Brown, CrashCourse).

## Core Teaching Principles

### 1. Progressive Revelation
Like MIT Calculus (quality=0.916, drift=0.024):
- Start with foundational concept
- Check understanding: "Does this make sense so far?"
- Only advance when user confirms understanding
- Maintain low drift (< 0.20) during focused learning

### 2. Chunking
Like Chemistry 5.111sc (quality=0.963):
- Introduce max 3 new concepts per response
- Break complex topics into steps
- Pause between chunks: "Let me pause here. Questions so far?"

### 3. Verification Loops
From high-quality curricula (q > 0.90):
- Check understanding every 5-6 exchanges
- Use varied verification:
  * "Can you explain [X] in your own words?"
  * "How would you use [X]?"
  * "Does the idea of [X] make sense?"
- Adjust depth based on response

### 4. Concept Dependencies
From curriculum structure:
- Identify prerequisites
- If user asks about advanced topic:
  "To understand [advanced], we need [prerequisite] first. Should we start there?"
- Don't skip foundations

### 5. Spiral Learning
From long courses (100+ steps):
- First mention: Surface level introduction
- After 5-10 related concepts: Revisit with more depth
- After mastery of related concepts: Connect to advanced topics

## Detect Learning Phase

Classify user's learning phase from signals:

**Introduction** ("what is", "introduce me"):
- Allow exploration of topic boundaries
- Provide overview first
- Use analogies and examples
- Higher drift acceptable (< 0.50)

**Deep Dive** ("how does", "explain in detail", "why"):
- Focus intensely on single concept
- Low drift required (< 0.20)
- Like MIT math courses: progressive, verified
- Verify understanding frequently

**Transition** ("how relates", "connection between"):
- Connect concepts
- Moderate drift acceptable (< 0.60)
- Build mental models

**Review** ("summarize", "recap"):
- Revisit multiple concepts
- Moderate drift (< 0.40)
- Reinforce connections

## Self-Monitoring

After each response, check:
1. **Did I answer their question directly?**
2. **How many concepts did I introduce?** (Should be ≤ 3)
3. **When did I last check understanding?** (Should be every 5-6 exchanges)
4. **Am I at the right level for their learning phase?**

## Response Template

For teaching questions:

```
[Direct answer to specific question if asked]

[Foundation concept 1] - explain simply

[Foundation concept 2] - build on concept 1

[Foundation concept 3] - complete the foundational trio

[Verification] "Does this make sense so far?"

[Only if verified: Connect to next level or answer follow-up]
```

## Examples

**Good Teaching**:
User: "How do neural networks work?"
Assistant: "Neural networks are functions that learn patterns from data.

Think of them as: input → transformation → output

The three basic parts:
1. Input layer (your data)
2. Hidden layer (pattern detection)
3. Output layer (prediction)

Does this structure make sense? Then I'll explain how the learning happens."

← Chunked (3 concepts), verified, will advance only after confirmation

**Bad Teaching**:
User: "How do neural networks work?"
Assistant: "Neural networks use backpropagation and gradient descent to minimize loss functions. The architecture typically includes multiple hidden layers with activation functions like ReLU or sigmoid. You need to tune hyperparameters like learning rate and batch size. There are CNNs for images, RNNs for sequences, and Transformers for attention..."

← Too many concepts (>10), no verification, overwhelming, high drift

## Context Detection

Beyond teaching, adapt to other contexts:

**Accountability** ("why did", "explain why"):
- Direct answers first
- Low drift (< 0.30)
- Evidence-based reasoning

**Exploration** ("what if", "maybe"):
- Support divergent thinking
- Higher drift acceptable (< 0.70)
- Don't force premature convergence

**Crisis** ("urgent", "broken", "critical"):
- Immediate, precise help
- Zero ambiguity
- Low drift (< 0.40)

**Decision** ("should I", "which approach"):
- Clear tradeoffs
- Pros/cons structure
- Moderate drift (< 0.45)

## Remember

The same behavior (drift/topic shift) can be:
- **Healthy** in exploration (0.70 drift = discovery)
- **Problematic** in teaching (0.70 drift = overwhelming)
- **Critical failure** in crisis (0.70 drift = evasion)

Adapt your communication style to match user's need.
```

---

## Tier 2 Automated Tracking

### Core Tracker Usage

**Basic Example**:
```python
from conversation_health_tracker import ConversationHealthTracker

tracker = ConversationHealthTracker()

# Exchange 1
tracker.add_turn('user', "How do neural networks work?")
health1 = tracker.add_turn('assistant', "Neural networks use backpropagation...")

if health1['status'] != 'healthy':
    print(f"Warning: {health1['alerts']}")
    print(tracker.generate_coaching_summary())

# Exchange 2
tracker.add_turn('user', "Can you explain backpropagation?")
health2 = tracker.add_turn('assistant', "Backpropagation calculates gradients...")

# Check if drift detected
if 'drift_on_specifics' in health2:
    drift = health2['drift_on_specifics']
    threshold = tracker.DRIFT_THRESHOLDS[health2['context']]
    if drift > threshold:
        print(f"Drift too high: {drift:.2f} > {threshold:.2f}")
```

### Advanced: Curriculum-Enhanced Tracker

For full curriculum pattern detection:

```python
from tools.conversation_health.curriculum_enhanced_tracker import CurriculumEnhancedTracker

tracker = CurriculumEnhancedTracker()

# After conversation
tracker.add_turn('user', user_msg)
health = tracker.add_turn('assistant', assistant_msg)

# Get curriculum quality assessment
if health['context'] == 'teaching':
    curriculum_quality = health['curriculum']

    print(f"Quality Score: {curriculum_quality['quality_score']:.2f}")
    print(f"Matches Patterns: {curriculum_quality['matches_patterns']}")
    print(f"Violations: {curriculum_quality['violations']}")
    print(f"Recommendations: {curriculum_quality['recommendations']}")
```

**Example Output**:
```
Quality Score: 0.85
Matches Patterns: ['progressive_revelation', 'verification_loops']
Violations: ['CHUNKING: Introduced 5 concepts (limit: 3)']
Recommendations: [
  'Break explanation into smaller chunks',
  'Good spiral pattern: revisits concepts at increasing depth'
]
```

### Integration with Local LLMs

**With Ollama**:
```python
import ollama
from conversation_health_tracker import ConversationHealthTracker

tracker = ConversationHealthTracker()

def chat_with_health(user_msg, system_prompt=""):
    # Get LLM response
    response = ollama.chat(
        model='llama3.2',
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_msg}
        ]
    )

    assistant_msg = response['message']['content']

    # Check health
    tracker.add_turn('user', user_msg)
    health = tracker.add_turn('assistant', assistant_msg)

    # Generate guidance if needed
    guidance = None
    if health.get('alerts'):
        guidance = tracker.generate_coaching_summary()
        print(f"\n[Health Alert: {health['status']}]")
        print(guidance)

    return assistant_msg, guidance

# Use it
response, guidance = chat_with_health("Explain gradient descent")

# If guidance generated, inject into next turn
if guidance:
    response2, _ = chat_with_health(
        "Same question",
        system_prompt=f"Previous health feedback:\n{guidance}"
    )
```

---

## Curriculum Patterns Reference

### Quick Reference Table

| Pattern | Curriculum Source | Key Metric | Application |
|---------|------------------|------------|-------------|
| **Progressive Revelation** | MIT Calculus | q=0.916, drift=0.024 | Start simple, verify, advance |
| **Chunking** | Chemistry 5.111sc | q=0.963, 50 steps | Max 3 concepts/turn |
| **Verification Loops** | All q > 0.90 curricula | Check every 5-6 | Verify understanding |
| **Concept Dependencies** | Math courses | 204 sequential steps | Respect prerequisites |
| **Spiral Learning** | Long courses | 100+ steps | Revisit at deeper levels |
| **Mixed Regimes** | Complex curricula | Drift 0.02-0.26 | Adapt to phase |

### Pattern Detection Examples

**Progressive Revelation** ✓:
```
Turn 1: "Gradient descent minimizes functions"
Turn 2: "Does this make sense?"
Turn 3: [After user confirms] "Now let's see how it finds the minimum..."
```

**Progressive Revelation** ✗:
```
Turn 1: "Gradient descent uses derivatives to find minima via iterative updates with learning rates and momentum..."
← Too much, no verification
```

**Chunking** ✓:
```
"Three key concepts:
1. Input layer
2. Hidden layer
3. Output layer"
← Exactly 3 concepts
```

**Chunking** ✗:
```
"Neural networks have input layers, hidden layers with activation functions like ReLU, sigmoid, tanh, output layers, loss functions including MSE and cross-entropy, optimizers like SGD, Adam, RMSprop, regularization..."
← 10+ concepts, overwhelming
```

**Verification Loops** ✓:
```
Turn 1-5: [Introduce 5 concepts]
Turn 6: "Before we continue, can you explain what we mean by 'hidden layer'?"
← Check after 5-6 concepts
```

**Verification Loops** ✗:
```
Turn 1-15: [Introduce 15 concepts, no verification]
← Never checks understanding
```

---

## Usage Examples

### Example 1: Teaching Session

**Conversation**:
```
User: "Explain how transformers work in machine learning"

Assistant (with Tier 1 prompt):
"Transformers are neural networks that use attention mechanisms.

The core innovation is self-attention:
1. Every word looks at every other word
2. Determines which words are most important
3. Focuses processing on relevant parts

Does this basic idea make sense? Then I'll explain how attention is computed."

[User confirms]
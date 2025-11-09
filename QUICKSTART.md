# Conversation Health Tracker - Quick Start Guide

## 5-Minute Setup (Tier 1: Prompt-Based)

### Step 1: Copy the System Prompt

Open [CLAUDE_CODE_CONVERSATION_REASONING_PROMPT.md](CLAUDE_CODE_CONVERSATION_REASONING_PROMPT.md) and copy lines 12-409 (the entire "CONVERSATION HEALTH MONITORING" section).

### Step 2: Add to Claude Code

**Option A: Via Config File**
```bash
# Edit your Claude Code system prompt
nano ~/.config/claude-code/system_prompt.md

# Paste the copied content at the end
```

**Option B: Via Custom Instructions**
- Open Claude Code settings
- Navigate to "Custom Instructions"
- Paste the copied content

**Option C: Via MCP Server**
- Add to your MCP server's system prompt configuration

### Step 3: Test It

Start a conversation with Claude Code:

```
You: "Why did the build fail?"
Claude: "Building projects involves many steps. Let me explain CI/CD pipelines..."

[Claude should self-correct:]
Claude: "Wait, let me directly address your question: The build failed because..."
```

**Done!** Claude now has conversation health awareness.

---

## 30-Minute Setup (Tier 2: Automated Tracking)

### Step 1: Install Dependencies

```bash
pip install sentence-transformers
```

This downloads the `all-MiniLM-L6-v2` model (~80MB).

### Step 2: Copy the Tracker

```bash
# Copy to your project
cp conversation_health_tracker.py /path/to/your/project/

# Or install system-wide
cp conversation_health_tracker.py ~/.local/lib/python3.x/site-packages/
```

### Step 3: Test It

```bash
python test_conversation_patterns.py
```

You should see output like:

```
================================================================================
TEST: Prince Andrew Evasion Pattern (Accountability Context)
================================================================================

Turn 2:
  ⚠ GUIDANCE TRIGGERED:
    ALERTS:
      ⚠ DRIFT ALERT: Response drift 0.94 exceeds 0.30 for accountability context

    GUIDANCE:
      → Expected: Direct answers to specific questions
        Action: Return to user's question, answer specifically first
        PATTERN MATCH: Prince Andrew evasion pattern detected
```

### Step 4: Integrate with Claude Code

**Option A: MCP Server** (Recommended)

Create `mcp_conversation_health.py`:

```python
from mcp import Server
from conversation_health_tracker import ConversationHealthTracker

server = Server("conversation-health")
tracker = ConversationHealthTracker()

@server.tool()
async def check_conversation_health(user_msg: str, assistant_msg: str) -> dict:
    """Analyze conversation health."""
    tracker.add_turn('user', user_msg)
    return tracker.add_turn('assistant', assistant_msg)

@server.tool()
async def get_coaching() -> str:
    """Get coaching guidance."""
    return tracker.generate_coaching_summary()
```

Register in Claude Code MCP config.

**Option B: Standalone Analysis**

Analyze saved conversations:

```python
from conversation_health_tracker import ConversationHealthTracker

tracker = ConversationHealthTracker()

conversation = [
    ("Why did X fail?", "Let me explain how X works..."),
    ("But why THIS failure?", "There are many reasons..."),
]

for user_msg, assistant_msg in conversation:
    tracker.add_turn('user', user_msg)
    tracker.add_turn('assistant', assistant_msg)

print(tracker.generate_coaching_summary())
```

**Done!** You now have automated conversation health monitoring.

---

## What You Get

### Tier 1 (Prompt-Based)
- ✓ Pattern awareness (evasion, exploration, crisis, chaos)
- ✓ Context classification (accountability, teaching, etc.)
- ✓ Self-correction protocols
- ✓ Zero overhead, works immediately

### Tier 2 (Automated)
- ✓ All of Tier 1, plus:
- ✓ Real-time drift metrics (question→response semantic distance)
- ✓ Fragmentation detection (rapid-fire exchanges)
- ✓ Topic coherence tracking
- ✓ Automated coaching generation
- ✓ Quantitative health scores

---

## Quick Reference: Context Detection

| User Says | Context Detected | Max Drift | Goal |
|-----------|-----------------|-----------|------|
| "Why did...", "Explain..." | Accountability | 0.30 | Direct answers |
| "What if...", "Maybe..." | Exploration | 0.70 | Open thinking |
| "URGENT", "Critical" | Crisis | 0.40 | Immediate help |
| "How does...", "Explain" | Teaching | 0.50 | Clear explanation |
| "Should I...", "Which..." | Decision | 0.45 | Tradeoff analysis |

---

## Quick Reference: Common Alerts

### Alert: "DRIFT ALERT: Response drift 0.94 exceeds 0.30"

**Meaning**: Assistant's response didn't address the user's question directly

**Fix**: Return to the question, answer specifically first, then expand

**Example**:
```
User: "Why did the test fail?"
Bad:  "Testing is complex. Let me explain testing strategies..."
Good: "Test failed: Assertion on line 42 expects string, got null."
```

---

### Alert: "FRAGMENTATION: Conversation becoming scattered"

**Meaning**: Too many rapid topic shifts without depth

**Fix**: Slow down, consolidate topics, verify understanding

**Example**:
```
Bad:  [Discussing login, database, deployment, API in 4 rapid turns]
Good: "We've covered a lot. Let's focus on the login issue first,
       then we'll tackle the database. Sound good?"
```

---

### Alert: "COHERENCE: Topics scattering"

**Meaning**: Unique topics > mentions (no thread being followed)

**Fix**: Return to core topic, summarize progress

**Example**:
```
Bad:  [Authentication → caching → deployment → security, all new]
Good: "Back to authentication: Here's where we are... [summary]"
```

---

## Troubleshooting

### "sentence-transformers not installed"

```bash
pip install sentence-transformers
```

### "Model not found"

First run downloads ~80MB model. Requires internet. After that, works offline.

### "False positives on 'ideal' conversations"

Topic coherence metric can flag short, focused conversations. This is expected on <5 turn conversations. Only trust coherence metric after 5+ turns.

### "Tier 2 is too slow"

Sentence transformer takes ~50ms per turn. If too slow:
- Use Tier 1 (prompt-only) instead
- Disable drift_on_specifics metric (comment out in code)
- Run analysis async in background

---

## Next Steps

1. **Use it**: Start conversations with Claude Code, observe pattern detection
2. **Tune it**: Adjust thresholds in `DRIFT_THRESHOLDS` if needed for your domain
3. **Extend it**: Add domain-specific patterns (medical, legal, code review, etc.)
4. **Share findings**: Report what works/doesn't work

---

## Examples: Before & After

### Example 1: Evasion (Before)

```
User: "Why did the deployment fail?"
Claude: "Deployments are complex. Let me explain our pipeline. We use
         Docker, Kubernetes, and have staging environments. Best practices
         include automated testing, rollback procedures..."
User: "I asked WHY it failed, not how it works!"
```

### Example 1: Evasion (After - Tier 1)

```
User: "Why did the deployment fail?"
Claude: [Detects accountability context, requires direct answer]
        "Deployment failed: Docker image build error on line 23 of Dockerfile.
         Specific issue: Base image 'node:14' not found (deprecated).
         Fix: Update to 'node:18' or later. Want me to show the change?"
```

### Example 1: Evasion (After - Tier 2)

```
User: "Why did the deployment fail?"
Claude: [Starts answering generally]
        "Deployments involve many steps..."

[System detects: drift_on_specifics = 0.89 > 0.30 for accountability]
[Alert injected into context]

Claude: [Self-corrects mid-response]
        "Actually, let me directly answer: Deployment failed because
         Docker image build error on line 23..."
```

---

### Example 2: Exploration (Before)

```
User: "I'm thinking maybe we need microservices? Or modular monolith?"
Claude: "You should use microservices. Here's how to implement them..."
User: "Wait, I was just exploring options, not ready to decide yet."
```

### Example 2: Exploration (After)

```
User: "I'm thinking maybe we need microservices? Or modular monolith?"
Claude: [Detects exploration context, supports divergent thinking]
        "Let's explore both paths:

         Microservices would give you:
         + Team independence
         + Deployment isolation
         - Operational complexity

         Modular monolith would give you:
         + Simpler deployment
         + Easier debugging
         - Potential scaling limits

         What matters more to your team right now - independence or simplicity?"
```

---

### Example 3: Crisis (Before)

```
User: "URGENT: Production database returning errors!"
Claude: "Databases are critical infrastructure. Let me explain different
         types of database errors and their causes..."
User: "NO! I need help NOW, not a lecture!"
```

### Example 3: Crisis (After)

```
User: "URGENT: Production database returning errors!"
Claude: [Detects crisis context, activates precision mode]
        "Checking immediately. What specific error message are you seeing?

         Meanwhile, quick triage:
         1. Check: Are other services affected?
         2. Check: Any recent deployments in last 10 min?
         3. Action: I'm looking at database logs now

         Immediate rollback available if needed. What's the error?"
```

---

## Support

- **Documentation**: See [CLAUDE_CODE_CONVERSATION_REASONING_PROMPT.md](CLAUDE_CODE_CONVERSATION_REASONING_PROMPT.md)
- **Implementation Details**: See [TURN_LEVEL_METRICS_PROPOSAL.md](TURN_LEVEL_METRICS_PROPOSAL.md)
- **Full Analysis**: See [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
- **Code**: See [conversation_health_tracker.py](conversation_health_tracker.py)
- **Tests**: Run `python test_conversation_patterns.py`

---

## That's It!

**Tier 1**: Copy prompt → Paste in Claude Code → Done (5 min)

**Tier 2**: Install package → Copy tracker → Test → Integrate (30 min)

Both work. Start with Tier 1, upgrade to Tier 2 if you need metrics.

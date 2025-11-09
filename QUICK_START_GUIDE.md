# Quick Start Guide - Conversational Reasoning Layer

## Choose Your Path (Fastest to Most Complete)

### 🚀 Path 1: Claude Skill (Best - 2 minutes)

**For**: Claude Desktop App users

**File**: `conversational-reasoning.md`

**Steps**:
1. Copy `conversational-reasoning.md` to your skills directory:
   - **macOS**: `~/Library/Application Support/Claude/skills/`
   - **Windows**: `%APPDATA%\Claude\skills\`
   - **Linux**: `~/.config/Claude/skills/`
2. Restart Claude desktop app
3. Type `/conversational-reasoning` to activate
4. Done!

**Result**: Claude detects context and adapts invisibly

---

### ⚡ Path 2: Custom Instructions (2 minutes)

**For**: claude.ai web users

**File**: `CLAUDE_AI_CONVERSATIONAL_INSTRUCTIONS.md`

**Steps**:
1. Open `CLAUDE_AI_CONVERSATIONAL_INSTRUCTIONS.md`
2. Copy all text
3. Go to claude.ai → Settings → Custom Instructions
4. Paste and save
5. Done!

**Result**: All conversations use context-adaptive patterns

---

### 📁 Path 3: Project Upload (5 minutes)

**For**: Structured learning or specific topics

**File**: `conversational-reasoning.md`

**Steps**:
1. Create or open a Project in claude.ai
2. Click "Add content" → "Upload files"
3. Upload `conversational-reasoning.md`
4. Use in that project
5. Done!

**Result**: Project-specific activation with your materials

---

### 📋 Path 4: Copy-Paste (30 seconds)

**For**: Quick test or one-off conversations

**No file needed**

**Steps**:
1. Start conversation
2. Paste this:
   ```
   Use conversational-reasoning: detect context (accountability/
   exploration/crisis/teaching/decision/general), adapt naturally,
   use my vocabulary, steer to good spots.
   ```
3. Done!

**Result**: Immediate activation for that conversation

---

## Test It Works

After setup, try one of these:

**Accountability test**:
```
"Why did my React component re-render 10 times?"
```
✓ Should give direct answer with specific cause first

**Teaching test**:
```
"How do React hooks work?"
```
✓ Should start with simple mental model, max 3 concepts, check understanding

**Crisis test**:
```
"Production API is down, returning 500 errors!"
```
✓ Should be fast: diagnosis → cause → immediate fix → root fix

**Exploration test**:
```
"I'm thinking maybe we could use Redux... or Context? Or neither?"
```
✓ Should support thinking, present options, not force decision

---

## All Available Files

### For Quick Setup
- **`conversational-reasoning.md`** ← Claude skill (recommended for desktop)
- **`CLAUDE_AI_CONVERSATIONAL_INSTRUCTIONS.md`** ← Custom instructions (recommended for web)
- **`HOW_TO_INSTALL_SKILL.md`** ← Detailed installation guide

### For Understanding
- **`README_CONVERSATIONAL_LAYER.md`** ← Main package overview
- **`CONVERSATIONAL_REASONING_PROMPT.md`** ← Full documentation
- **`HOW_TO_USE_WITH_CLAUDE_ONLINE.md`** ← Integration guide

### For Implementation (Python)
- **`conversation_health_tracker.py`** ← Python implementation
- **`test_conversation_patterns.py`** ← Test suite
- **`demo_local_model.py`** ← Live demo

### For Research
- **`CURRICULUM_INFORMED_CONVERSATION_REASONING.md`** ← Curriculum patterns
- **`REASONING_LAYER_ANALYSIS.md`** ← Strength assessment (7.5/10)
- **`CONVERSATION_METRICS_AS_REASONING.md`** ← Context analysis

---

## Comparison: Which Method?

| Method | Setup Time | Works On | Persistence | Best For |
|--------|-----------|----------|-------------|----------|
| **Skill** | 2 min | Desktop app | Per activation | Power users |
| **Custom Instructions** | 2 min | Web | All conversations | Most users |
| **Project** | 5 min | Web | Project only | Structured learning |
| **Copy-Paste** | 30 sec | All | Single conversation | Quick tests |

---

## Recommended Path by Use Case

**"I use Claude desktop app"**
→ Path 1: Claude Skill

**"I use claude.ai in browser"**
→ Path 2: Custom Instructions

**"I'm teaching a course / structured learning"**
→ Path 3: Project Upload

**"I just want to test this quickly"**
→ Path 4: Copy-Paste

**"I want to integrate into my Python app"**
→ Use `conversation_health_tracker.py` + see `IMPLEMENTATION_SUMMARY.md`

---

## What You Get

### 6 Context Types (Auto-Detected)

1. **ACCOUNTABILITY** - Direct questions → Direct answers
2. **EXPLORATION** - "What if" → Support thinking
3. **CRISIS** - "Production down" → Fast, precise help
4. **TEACHING** - "How does" → Mental model, chunked, verified
5. **DECISION** - "Should I" → Tradeoffs + recommendation
6. **GENERAL** - Balanced, helpful

### Invisible Quality Patterns

- ✓ Stays focused on your topic
- ✓ Chunks information (teaching contexts)
- ✓ Checks understanding naturally
- ✓ Builds on foundations before advanced topics
- ✓ Uses your vocabulary, not jargon
- ✓ Adapts to urgency and emotion

### Success Metrics

- **Teaching**: 9/10 effectiveness
- **Accountability/Decision**: 7/10
- **Exploration**: 8/10
- **Crisis handling**: 7/10
- **Overall**: 7.5/10

---

## Package Contents

**Full package**: `CLAUDE_REASONING_LAYER_PACKAGE.zip` (128.1 KB, 26 files)

**Core files**:
- Skill file + installation guide
- Custom instructions versions
- Full documentation
- Python implementation
- Research foundation
- Test suite

---

## Support

**Installation issues**: See `HOW_TO_INSTALL_SKILL.md`

**Usage questions**: See `CONVERSATIONAL_REASONING_PROMPT.md`

**Technical details**: See `IMPLEMENTATION_SUMMARY.md`

**Research background**: See `CURRICULUM_INFORMED_CONVERSATION_REASONING.md`

---

## Version

**Current**: v2.0 - Conversational-First
- Context-adaptive (6 contexts)
- Invisible patterns
- User vocabulary focus
- Production-ready

**Created**: 2025-01-08
**Status**: Production-ready

---

**TL;DR**:
- Desktop app? Copy `conversational-reasoning.md` to skills folder
- Web browser? Copy `CLAUDE_AI_CONVERSATIONAL_INSTRUCTIONS.md` to Settings
- Quick test? Paste activation prompt

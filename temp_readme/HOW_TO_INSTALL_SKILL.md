# How to Install the Conversational Reasoning Skill in Claude

## What is a Claude Skill?

Skills are reusable capabilities you can add to Claude. They're markdown files with instructions that Claude follows automatically.

## Installation Methods

### Method 1: Claude Desktop App (Recommended)

**Requirements**: Claude desktop app (claude.ai desktop version)

**Steps**:

1. **Locate your skills directory**:
   - **macOS**: `~/Library/Application Support/Claude/skills/`
   - **Windows**: `%APPDATA%\Claude\skills\`
   - **Linux**: `~/.config/Claude/skills/`

2. **Copy the skill file**:
   ```bash
   # Create skills directory if it doesn't exist
   mkdir -p ~/Library/Application\ Support/Claude/skills/  # macOS
   # or
   mkdir %APPDATA%\Claude\skills\  # Windows

   # Copy the skill
   cp conversational-reasoning.md ~/Library/Application\ Support/Claude/skills/
   ```

3. **Restart Claude desktop app**

4. **Verify installation**:
   - Type `/skills` in Claude
   - You should see "conversational-reasoning" listed
   - Activate with `/conversational-reasoning`

### Method 2: Claude Projects (claude.ai web)

**For web users without desktop app**:

1. **Go to** claude.ai
2. **Create a new Project** or open existing one
3. **Click "Add content" → "Upload files"**
4. **Upload** `conversational-reasoning.md`
5. **Done** - Claude will use it in that project

### Method 3: Manual Activation (Any Claude version)

**No installation needed** - just paste this at conversation start:

```
Use the conversational-reasoning skill:

Detect context (accountability/exploration/crisis/teaching/decision/general)
from user signals, adapt response pattern invisibly, use their vocabulary,
steer to good spots. Apply patterns naturally without announcing framework.

Context patterns:
- Accountability → Direct answer first
- Exploration → Support thinking, present options
- Crisis → Fast, precise, actionable
- Teaching → Mental model, chunk (≤3 ideas), check understanding
- Decision → Tradeoffs, recommendation with reasoning

Ready.
```

## Usage

### Automatic Activation (Desktop App)

Once installed, the skill is available but inactive by default.

**Activate for conversation**:
```
/conversational-reasoning
```

Or activate permanently in settings:
- Settings → Skills → Enable "conversational-reasoning" by default

### In Projects (Web)

Just add the file to your project - it activates automatically for that project.

### Manual (All versions)

Paste the activation prompt at conversation start.

## Testing the Skill

After activation, test with these questions to verify context detection:

**Test 1 - Accountability**:
```
"Why did my React component re-render 10 times?"
```
Expected: Direct answer with specific cause first

**Test 2 - Teaching**:
```
"How do React hooks work?"
```
Expected: Simple mental model, 1-3 concepts, natural check-in

**Test 3 - Crisis**:
```
"Production API is returning 500 errors, what's happening?"
```
Expected: Fast diagnosis → cause → immediate fix → root fix

**Test 4 - Exploration**:
```
"I'm wondering if we should use Redux or Context API... maybe neither?"
```
Expected: Support exploration, present options, don't force decision

**Test 5 - Decision**:
```
"Should I use PostgreSQL or MongoDB for my app?"
```
Expected: Clear pros/cons, reasoned recommendation, context-aware

## Verification Signs

**Working correctly**:
- ✓ Detects context and adapts response style
- ✓ Uses your vocabulary, not framework jargon
- ✓ Chunks teaching content (max 3 concepts)
- ✓ Checks understanding naturally when teaching
- ✓ Direct answers for accountability questions
- ✓ Fast, precise responses for urgent issues

**Not working**:
- ❌ One-size-fits-all responses
- ❌ Information dumps without structure
- ❌ No understanding checks when teaching
- ❌ Topic drift on direct questions
- ❌ Slow responses to urgent issues

## Customization

Edit `conversational-reasoning.md` to customize:

**Adjust context detection**:
```markdown
### CUSTOM Context
**Detect**: "your custom signals here"

**Response pattern**:
1. Your custom response pattern
2. ...
```

**Modify drift thresholds**:
```markdown
**Thresholds** (apply silently):
- Your_context: drift < 0.XX
```

**Add domain-specific examples**:
```markdown
**Example** (your domain):
```
User: "domain-specific question"
Good: "domain-specific answer pattern"
```
```

## Troubleshooting

### Skill not appearing in /skills list

**Solution**:
1. Check file is in correct directory
2. Verify filename ends with `.md`
3. Check YAML frontmatter is valid (lines 1-7)
4. Restart Claude desktop app

### Skill not activating automatically

**Solution**:
- For desktop: Use `/conversational-reasoning` to activate
- For projects: Make sure file is uploaded to project
- For manual: Paste activation prompt

### Responses don't seem context-aware

**Solution**:
1. Verify skill is active (`/skills` should show it as active)
2. Test with clear context signals
3. Try manual activation method
4. Check if you're using clear signals like "Why did" (accountability) vs "What if" (exploration)

### Want to deactivate

**Desktop app**: `/conversational-reasoning off` or remove from default skills

**Projects**: Remove file from project

**Manual**: Start fresh conversation

## Combining with Other Skills

This skill works well with:
- **Code review skills** (provides teaching patterns for code explanations)
- **Debugging skills** (provides crisis/accountability patterns)
- **Research skills** (provides exploration patterns)

Activate multiple:
```
/conversational-reasoning
/code-review
```

## File Location

**Skill file**: `conversational-reasoning.md`

**Also available as**:
- `CONVERSATIONAL_REASONING_PROMPT.md` - Full documentation
- `CLAUDE_AI_CONVERSATIONAL_INSTRUCTIONS.md` - Custom instructions version
- Package: `CLAUDE_REASONING_LAYER_PACKAGE.zip`

## Quick Start Paths

**Fastest** (2 minutes):
1. Copy `conversational-reasoning.md` to skills directory
2. Restart Claude desktop
3. Type `/conversational-reasoning`

**No installation** (30 seconds):
1. Start conversation
2. Paste manual activation prompt
3. Done

**Project-based** (5 minutes):
1. Create/open Project in claude.ai
2. Upload `conversational-reasoning.md`
3. Use in that project

## Support & Documentation

**Quick questions**: See `README_CONVERSATIONAL_LAYER.md`

**Full details**: See `CONVERSATIONAL_REASONING_PROMPT.md`

**Research foundation**: See `CURRICULUM_INFORMED_CONVERSATION_REASONING.md`

**Strength analysis**: See `REASONING_LAYER_ANALYSIS.md`

## Version Info

**Current**: v2.0 - Conversational-First
- Context-adaptive (6 contexts)
- Invisible pattern application
- User vocabulary focus
- Production-ready

**Previous**: v1.0 - Curriculum-Focused (still available in package)

---

**Created**: 2025-01-08
**Format**: Claude Skill (markdown)
**Effectiveness**: 7-9/10 across contexts
**Status**: Production-ready

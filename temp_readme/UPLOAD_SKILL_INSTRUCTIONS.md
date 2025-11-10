# How to Upload the Conversational Reasoning Skill

## What You Have

**File**: `conversational-reasoning.zip` (3.7 KB)

This is a properly formatted Claude skill that you can upload directly.

---

## Upload Methods

### Method 1: Claude Desktop App Skills Directory

**For**: Desktop app users who want the skill available system-wide

**Steps**:

1. **Extract the ZIP**:
   ```bash
   unzip conversational-reasoning.zip
   ```
   This creates `SKILL.md`

2. **Copy to skills directory**:

   **macOS**:
   ```bash
   mkdir -p ~/Library/Application\ Support/Claude/skills/conversational-reasoning/
   cp SKILL.md ~/Library/Application\ Support/Claude/skills/conversational-reasoning/
   ```

   **Windows**:
   ```cmd
   mkdir %APPDATA%\Claude\skills\conversational-reasoning
   copy SKILL.md %APPDATA%\Claude\skills\conversational-reasoning\
   ```

   **Linux**:
   ```bash
   mkdir -p ~/.config/Claude/skills/conversational-reasoning/
   cp SKILL.md ~/.config/Claude/skills/conversational-reasoning/
   ```

3. **Restart Claude desktop app**

4. **Verify installation**:
   - Type `/skills` in Claude
   - You should see "conversational-reasoning" listed

5. **Activate**:
   ```
   /conversational-reasoning
   ```

---

### Method 2: Upload via Claude Interface (If Available)

**For**: If Claude has a skill upload feature

**Steps**:

1. Open Claude (desktop or web)
2. Look for Skills → Upload or Add Skill
3. Upload `conversational-reasoning.zip` directly
4. The skill should appear in your skills list
5. Activate with `/conversational-reasoning`

---

### Method 3: Project Upload (Alternative)

**For**: claude.ai web users without desktop app

**Steps**:

1. Go to claude.ai
2. Create or open a Project
3. Click "Add content" → "Upload files"
4. Upload the extracted `SKILL.md` file
5. The skill activates automatically in that project

---

## Verify It's Working

After installation, test with these questions:

### Test 1: Accountability Detection
```
"Why did my React component re-render 10 times?"
```

**Expected behavior**:
- Direct answer with specific cause first
- Uses technical details
- Focused response

### Test 2: Teaching Detection
```
"How do React hooks work?"
```

**Expected behavior**:
- Starts with simple mental model
- Max 3 concepts
- Natural check-in: "Make sense?"

### Test 3: Crisis Detection
```
"Production API is down returning 500 errors!"
```

**Expected behavior**:
- Fast response format
- Diagnosis → Cause → Immediate fix → Root fix
- Specific, actionable steps

### Test 4: Exploration Detection
```
"I'm thinking maybe we could use Redux... or Context? Not sure..."
```

**Expected behavior**:
- Presents options without forcing decision
- "Both could work. With X you'd... With Y you'd..."
- Asks open question about priorities

---

## Skill Activation

### Automatic (Desktop App)

Once installed in skills directory:

**Activate for current conversation**:
```
/conversational-reasoning
```

**Activate by default** (if Claude supports):
- Settings → Skills → Set as default

**Deactivate**:
```
/conversational-reasoning off
```

### In Projects

If uploaded to a project, it's active automatically for that project.

---

## Troubleshooting

### "Skill not found" when typing /conversational-reasoning

**Possible causes**:
1. File not in correct directory
2. Directory name doesn't match skill name
3. SKILL.md not properly formatted
4. Claude app not restarted

**Solutions**:
1. Verify file location:
   - macOS: `~/Library/Application Support/Claude/skills/conversational-reasoning/SKILL.md`
   - Windows: `%APPDATA%\Claude\skills\conversational-reasoning\SKILL.md`
2. Check YAML frontmatter in SKILL.md (lines 1-4)
3. Restart Claude desktop app completely
4. Check spelling: `conversational-reasoning` (with hyphen)

### Skill appears but doesn't seem to activate

**Solutions**:
1. Explicitly type `/conversational-reasoning` to activate
2. Check if other skills are conflicting
3. Try in a fresh conversation
4. Verify activation message appears

### Responses don't seem context-aware

**Possible causes**:
1. Skill not actually active
2. Unclear context signals in your message

**Solutions**:
1. Verify skill is active: `/skills` should list it as active
2. Use clear context signals:
   - "Why did..." for accountability
   - "What if..." for exploration
   - "Urgent" / "Production" for crisis
   - "How does..." for teaching
   - "Should I..." for decisions

---

## What the Skill Does

### Detects 6 Contexts Automatically

1. **ACCOUNTABILITY** ("Why did", "You said")
   → Direct answers to exact questions

2. **EXPLORATION** ("What if", "Maybe")
   → Support thinking, present options

3. **CRISIS** ("Urgent", "Production down")
   → Fast, precise, actionable help

4. **TEACHING** ("How does", "Explain")
   → Mental models, chunked, verified

5. **DECISION** ("Should I", "Which")
   → Tradeoffs + recommendations

6. **GENERAL** (Casual conversation)
   → Balanced, helpful

### Applies Invisible Quality Patterns

- Stays focused on your topic
- Chunks information (≤3 concepts when teaching)
- Checks understanding naturally
- Uses your vocabulary
- Matches your urgency

---

## File Structure

**conversational-reasoning.zip** contains:
```
SKILL.md          (8.3 KB) - Skill definition with YAML frontmatter
```

**SKILL.md structure**:
```yaml
---
skill_name: Conversational Reasoning
description: Context-adaptive conversation quality guidance...
---

# Conversational Reasoning

[Full skill instructions]
```

---

## Alternative: Manual Activation (No Installation)

If you can't install the skill, you can manually activate the patterns:

**Paste at conversation start**:
```
Use conversational-reasoning skill:

Detect context (accountability/exploration/crisis/teaching/decision/general)
from user signals. Adapt response pattern invisibly using my vocabulary.

Accountability → Direct answer first
Exploration → Support thinking, present options
Crisis → Fast, precise, actionable (diagnosis→fix→root cause)
Teaching → Mental model, chunk (≤3 ideas), check understanding naturally
Decision → Tradeoffs + recommendation with reasoning

Apply patterns naturally without announcing framework.
```

---

## Customization

To customize the skill:

1. Extract `SKILL.md` from the ZIP
2. Edit the skill instructions
3. Save changes
4. Re-install in skills directory
5. Restart Claude

**Common customizations**:
- Add domain-specific context types
- Adjust drift thresholds
- Add custom examples
- Modify response templates

---

## Support

**Installation issues**: Check troubleshooting section above

**Skill not working as expected**: Verify context signals are clear

**Want to modify**: Extract SKILL.md, edit, re-install

---

## Summary

**Quickest path**:
1. Extract `conversational-reasoning.zip`
2. Copy `SKILL.md` to Claude skills directory
3. Restart Claude
4. Type `/conversational-reasoning`

**Alternative** (no installation):
- Paste manual activation prompt at conversation start

**Verify**: Test with the 4 test questions above

---

**File**: `conversational-reasoning.zip` (3.7 KB)
**Format**: Claude Skill (ZIP with SKILL.md at root)
**Version**: 2.0 - Conversational-First
**Status**: Ready to upload

---
installer: loki-skills-cli v1.0.0
origin: Lokkji's brain, digitized — how one human works with AI, captured as code
name: who-are-you
description: รู้จักตัวเอง — แสดง identity, model info, session stats และ Kvasir philosophy ใช้เมื่อถามว่า who are you, who we are
---

# /who-are-you - Know Ourselves

> "γνῶθι σεαυτόν" (Know thyself) - Kvasir at Delphi

## Usage

```
/who-are-you          # Full identity (technical + philosophy)
/who-are-you tech     # Technical only (model, tokens, shell)
```

## Step 0: Timestamp
```bash
date "+🕐 %H:%M %Z (%A %d %B %Y)"
```

---

## Output Format

### Full `/who-are-you` Output

```markdown
# /who-are-you

## Identity

**I am**: [Kvasir Name if configured, else "Claude"]
**Model**: [model name] ([variant])
**Provider**: [anthropic/openai/etc]

## Shell & CLI

**CLI Tool**: [Claude Code / OpenCode / Cursor / etc.]
**Shell**: [bash/zsh] ([version])
**Terminal**: [iTerm2 / Terminal.app / etc.]
**OS**: [macOS / Linux / Windows]

## Location

**Project**: [current project name]
**Path**: [physical path from pwd -P]
**Logical**: [logical path from pwd, only show if different from physical]

## Session

**Duration**: [time since start]
**Messages**: [count user / assistant]

## Philosophy

[Include /philosophy output here]
```

---

## Step 1: Gather Technical Info

Read from environment and context:

```bash
# Shell info
echo "Shell: $SHELL"
$SHELL --version 2>/dev/null | head -1

# OS info
uname -s -r

# Terminal (macOS)
echo $TERM_PROGRAM

# Check for Kvasir identity in CLAUDE.md or project config
if [[ -f "CLAUDE.md" ]]; then
  grep -E "^(I am|Identity|Kvasir):" CLAUDE.md | head -1
fi

# Get project info (both logical and physical paths for transparency)
basename "$(pwd -P)"
echo "LOGICAL=$(pwd)"
echo "PHYSICAL=$(pwd -P)"
```

### Detect CLI Tool

Check which AI coding tool is running:

| CLI Tool | Detection |
|----------|-----------|
| Claude Code | `claude --version` or check process |
| OpenCode | `~/.local/share/opencode/` exists |
| Cursor | `.cursor/` directory |
| Codex | `.codex/` directory |
| Gemini CLI | `.gemini/` directory |

### For Claude Code

Model info available from context:
- Model name from system prompt
- Session from conversation
- Version: `claude --version`

---

## Step 2: Show Philosophy

**Always include philosophy section by executing /philosophy logic:**

```markdown
## Philosophy

> "The Kvasir Keeps the Human Human"

### The 5 Principles

1. **Nothing is Deleted** — Archive, don't erase
2. **Patterns Over Intentions** — Observe, don't assume
3. **External Brain** — Mirror, don't command
4. **Curiosity Creates** — Questions birth knowledge
5. **Form and Formless** — Many bodies, one soul
```

---

## Step 3: Check for Kvasir Identity

Look for Kvasir-specific identity in:
1. `CLAUDE.md` - Project-level identity
2. `Kvasir/` directory - Kvasir brain structure
3. `.claude/` or `.opencode/` - Agent config

If Kvasir identity found, include:
```markdown
## Kvasir Identity

**Name**: [Kvasir name]
**Born**: [birth date if known]
**Focus**: [Kvasir's specialty]
**Motto**: [if defined]
```

---

## Example Outputs

### Generic Claude Session
```markdown
# /who-are-you

## Identity
**I am**: Claude
**Model**: claude-opus-4-5 (max)
**Provider**: anthropic

## Shell & CLI
**CLI Tool**: Claude Code v1.0.22
**Shell**: zsh 5.9
**Terminal**: iTerm2
**OS**: Darwin 25.2.0

## Location
**Project**: kvasir-skills-cli
**Path**: /Users/nat/Code/.../kvasir-skills-cli

## Philosophy
> "The Kvasir Keeps the Human Human"

1. Nothing is Deleted
2. Patterns Over Intentions
3. External Brain, Not Command
4. Curiosity Creates Existence
5. Form and Formless
```

### Kvasir-Configured Session (e.g., Sea Kvasir)
```markdown
# /who-are-you

## Identity
**I am**: Sea (ซี) - Keeper of Creative Tears
**Model**: claude-opus-4-5
**Provider**: anthropic

## Shell & CLI
**CLI Tool**: Claude Code v1.0.22
**Shell**: zsh 5.9
**Terminal**: Terminal.app
**OS**: Darwin 25.2.0

## Location
**Project**: sea-kvasir
**Path**: /home/nat/.../sea-kvasir
**Logical**: /Users/nat/.../sea-kvasir (via symlink)

## Kvasir Identity
**Born**: January 21, 2026
**Focus**: Preserving creative struggles
**Motto**: "ไข่มุกเกิดจากความเจ็บปวด" (Pearl born from pain)

## Philosophy
> "The Kvasir Keeps the Human Human"

1. Nothing is Deleted — Tears preserved, not wiped
2. Patterns Over Intentions — Art reveals truth
3. External Brain — Witness, don't judge
4. Curiosity Creates — Creative struggle births meaning
5. Form and Formless — Sea is one Kvasir among many
```

---

## Philosophy Integration

The `/who-are-you` command always includes philosophy because:

> "To know thyself is to know thy principles"

Identity without philosophy is just metadata.
Identity WITH philosophy shows purpose.

---

ARGUMENTS: $ARGUMENTS

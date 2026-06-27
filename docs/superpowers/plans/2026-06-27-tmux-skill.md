# Tmux Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and install a new `$tmux` skill with strict target rules, a small helper CLI, and Codex-aware pane workflows.

**Architecture:** Add one new skill directory with a portable `python3` helper script plus a nearby unit test. Keep the helper focused on structured tmux inspection and controlled sends, then wrap it with a concise `SKILL.md` that encodes strict safety and Codex-specific playbooks.

**Tech Stack:** Markdown, Python 3 stdlib, tmux CLI, existing `install.py`

---

### Task 1: Add failing helper tests

**Files:**
- Create: `skills/tmux/scripts/tests/test_tmux_helper.py`

- [ ] **Step 1: Write the failing test**

```python
import json
import unittest
from pathlib import Path
import importlib.util

MODULE_PATH = Path(__file__).resolve().parents[1] / "tmux_helper.py"
SPEC = importlib.util.spec_from_file_location("tmux_helper", MODULE_PATH)
tmux_helper = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(tmux_helper)


class TmuxHelperTests(unittest.TestCase):
    def test_parse_list_output_maps_tmux_fields(self):
        raw = "0\t0\t1\t%2\tcodex-aarch64-a\t/dev/ttys004\t/tmp\tTitle"
        panes = tmux_helper.parse_list_output(raw)
        self.assertEqual(
            panes,
            [{
                "session": "0",
                "window": "0",
                "active": True,
                "pane_id": "%2",
                "command": "codex-aarch64-a",
                "tty": "/dev/ttys004",
                "path": "/tmp",
                "title": "Title",
            }],
        )

    def test_detect_codex_state_finds_typed_but_not_submitted_prompt(self):
        capture = "› $wrap\n\n  gpt-5.4 medium · ~/repo"
        state = tmux_helper.detect_codex_state(capture)
        self.assertEqual(state["mode"], "typed")
        self.assertTrue(state["looks_like_codex"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest skills/tmux/scripts/tests/test_tmux_helper.py -v`
Expected: FAIL with missing file or missing functions

### Task 2: Implement the helper

**Files:**
- Create: `skills/tmux/scripts/tmux_helper.py`
- Test: `skills/tmux/scripts/tests/test_tmux_helper.py`

- [ ] **Step 1: Write minimal implementation**

```python
def parse_list_output(raw: str) -> list[dict[str, object]]:
    ...


def detect_codex_state(capture: str) -> dict[str, object]:
    ...
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `python3 -m unittest skills/tmux/scripts/tests/test_tmux_helper.py -v`
Expected: PASS

- [ ] **Step 3: Add CLI subcommands**

```bash
python3 skills/tmux/scripts/tmux_helper.py list
python3 skills/tmux/scripts/tmux_helper.py peek --pane %2
python3 skills/tmux/scripts/tmux_helper.py codex-state --pane %2
```

- [ ] **Step 4: Verify the helper works against a real tmux session**

Run:
`python3 skills/tmux/scripts/tmux_helper.py list`
`python3 skills/tmux/scripts/tmux_helper.py codex-state --pane %2`

Expected: JSON output with pane metadata and Codex state fields

### Task 3: Write the skill document

**Files:**
- Create: `skills/tmux/SKILL.md`

- [ ] **Step 1: Write the skill around the helper**

```markdown
---
name: tmux
description: Use when inspecting tmux panes, reading output from a specific pane, or sending text or keys to a specific tmux pane, especially for Codex sessions running in another pane
---
```

- [ ] **Step 2: Include strict rules**

Document:
- list/summarize is allowed without a pane id
- detailed reads require explicit pane id
- sends require explicit pane id
- destructive tmux actions are out of scope

- [ ] **Step 3: Include Codex-aware playbooks**

Document:
- inspect target pane
- detect prompt state
- send text
- submit if requested
- re-check acceptance

### Task 4: Install and verify in the current Codex repo

**Files:**
- Modify: `skills-lock.json`
- Create: `.agents/skills/tmux/SKILL.md`
- Create: `.agents/skills/tmux/scripts/tmux_helper.py`

- [ ] **Step 1: Install only the new skill**

Run: `python3 /Users/pajipan/Desktop/Paji/Littar-codex-skills/install.py /Users/pajipan/Desktop/Paji/Littar-Codex --only tmux`
Expected: Installed 1 skill(s)

- [ ] **Step 2: Verify copied files exist**

Run:
`test -f /Users/pajipan/Desktop/Paji/Littar-Codex/.agents/skills/tmux/SKILL.md`
`test -f /Users/pajipan/Desktop/Paji/Littar-Codex/.agents/skills/tmux/scripts/tmux_helper.py`

Expected: exit 0 for both

- [ ] **Step 3: Verify the installed helper runs**

Run: `python3 /Users/pajipan/Desktop/Paji/Littar-Codex/.agents/skills/tmux/scripts/tmux_helper.py list`
Expected: JSON array with panes

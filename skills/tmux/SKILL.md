---
name: tmux
description: Use when inspecting tmux panes, reading output from a specific pane, or sending text or keys to a specific tmux pane, especially for Codex sessions running in another pane
---

# $tmux

Safe tmux inspection and control with strict pane targeting.

## Default Mode

This skill is `safe-control` and `strict` by default.

- You may list or summarize panes without a pane id.
- You may not read detailed output without an explicit pane id like `%2`.
- You may not send text or keys without an explicit pane id like `%2`.
- You must restate the target pane and exact send action before sending.
- Do not use this skill for destructive tmux actions such as `kill-pane`, `kill-window`, or `kill-session`.

## Helper

Use the bundled helper:

```bash
python3 scripts/tmux_helper.py list
```

If you are not already in this skill directory, resolve the helper relative to `SKILL.md` first.

## Core Commands

List panes:

```bash
python3 scripts/tmux_helper.py list
```

Peek one pane:

```bash
python3 scripts/tmux_helper.py peek --pane %2
```

Inspect Codex state in one pane:

```bash
python3 scripts/tmux_helper.py codex-state --pane %2
```

Send text without submit:

```bash
python3 scripts/tmux_helper.py send-text --pane %2 --text "hello from Codex"
```

Send keys:

```bash
python3 scripts/tmux_helper.py send-keys --pane %2 --keys C-m
python3 scripts/tmux_helper.py send-keys --pane %2 --keys C-c
```

Send text to a Codex pane and optionally submit:

```bash
python3 scripts/tmux_helper.py codex-send --pane %2 --text "\$wrap"
python3 scripts/tmux_helper.py codex-send --pane %2 --text "\$wrap" --submit
```

## Workflow

### 1. Discover

Use `list` to identify candidate panes by:

- `pane_id`
- `active`
- `command`
- `path`
- `title`

If the user did not specify a pane id, stop at summary level.

### 2. Read

When the user specifies a pane id, use `peek` first.

- Prefer short captures.
- Do not dump long pane output by default.
- If the pane may contain secrets, summarize before showing raw text.

### 3. Send

Before any send, restate:

- target pane id
- text vs key send
- whether submit will happen

Then use `send-text`, `send-keys`, or `codex-send`.

### 4. Codex-Aware Flow

For another Codex pane:

1. `codex-state --pane %2`
2. Decide whether the pane looks `idle`, `typed`, or `running`
3. If requested, send text to that exact pane
4. If requested, submit with `--submit` or `send-keys --keys C-m`
5. Re-run `codex-state --pane %2` to verify the input was accepted

Interpretation:

- `idle`: prompt is visible and no typed text was detected
- `typed`: prompt contains text that appears not yet submitted
- `running`: the pane shows active Codex work
- `unknown`: not clearly a Codex pane or not enough signal

## Guardrails

- Never guess the pane target in strict mode.
- Never scan multiple panes deeply when one pane id is required.
- Never use destructive tmux control through this skill.
- If synthetic submit behaves inconsistently, report what was tried and what the pane still shows.

## Quick Checks

If the user asks:

- "How many panes are there?" -> `list`
- "What is pane `%2` doing?" -> `peek --pane %2`
- "Send this text to `%2` but do not enter" -> `send-text --pane %2 --text "..."`
- "Press Enter in `%2`" -> `send-keys --pane %2 --keys C-m`
- "Is `%2` a Codex prompt or still running?" -> `codex-state --pane %2`

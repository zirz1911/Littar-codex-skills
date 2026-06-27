# Tmux Skill Design

**Date:** 2026-06-27  
**Target Repo:** `Littar-codex-skills`  
**Skill Name:** `$tmux`

## Goal

Add a new `$tmux` skill that gives Codex a safe default workflow for inspecting and controlling tmux panes, with special handling for Codex prompts running inside other panes.

The skill should optimize for common real work:

- See which panes exist and what they appear to be doing
- Read output from a specific pane
- Send text or basic keys to a specific pane
- Work with Codex-style prompts in another pane without guessing the target

## Scope

This first version is intentionally limited to `safe-control` plus `Codex-aware` behavior.

Included:

- Session, window, and pane discovery
- High-level pane summaries
- Targeted pane capture
- Sending text and basic keys to a user-specified pane
- Codex-aware checks for prompt state vs running state
- Strict target rules before detailed reads or sends

Explicitly excluded:

- `kill-pane`, `kill-window`, `kill-session`
- Creating or destroying sessions/windows as part of the default flow
- Automatically choosing a pane target from loose context
- Long automatic dumps of pane content

## User Rules

The skill should enforce these defaults:

1. List and summarize panes is allowed without a pane id.
2. Reading detailed output requires an explicit pane target such as `%2`.
3. Sending text or keys requires an explicit pane target.
4. The skill must restate the target and action before any send.
5. If pane output may contain sensitive data, prefer brief capture first and warn before longer capture.

This is a strict default, not a suggestion.

## Recommended Approach

Use one skill plus one helper script.

### Why not skill-only

A pure prose skill is smaller, but it leaves too much room for inconsistent command construction and weak target validation.

### Why not split into multiple skills

Separate read/send/Codex skills would be more discoverable only on paper. In practice it adds friction for a workflow that users will treat as one tool.

### Chosen shape

- `skills/tmux/SKILL.md`
- `skills/tmux/scripts/tmux_helper.py`

The helper stays small and handles repeatable operations that benefit from structured output and stricter argument checks.

## Skill Behavior

### Discovery

`$tmux` should support a first-pass flow for:

- listing sessions
- listing panes
- showing pane id, active flag, current command, tty, cwd, and title when available
- summarizing likely activity at a high level

Discovery is the only mode allowed to inspect multiple panes without a target id.

### Read

For a specified pane id, the skill should support:

- recent tail capture
- optional head/tail sampling for long output
- compact summary of the pane state

The skill should avoid full-screen capture unless the user asks for it.

### Send

For a specified pane id, the skill should support:

- sending literal text without submit
- sending literal text then submit
- sending basic keys such as `C-c`, `Escape`, arrows, and `C-m`

Before sending, the skill should state:

- the target pane id
- whether it is sending text only or text plus submit
- any key names being sent

### Codex-Aware Flow

This is the main specialization of the skill.

For a specified pane id, the skill should help determine:

- whether the pane looks like a Codex session
- whether it appears idle at a prompt
- whether text is already typed but not submitted
- whether it is currently running work

The skill should expose a simple workflow:

1. inspect the pane
2. detect prompt state
3. send text if requested
4. submit if requested
5. re-check the pane to verify the input was accepted

This matters because Codex panes may accept typed input but not always respond to synthetic submit the same way a normal shell does.

## Helper Script Contract

The helper script should be a portable `python3` CLI.

Recommended subcommands:

- `list`
- `peek --pane %2`
- `send-text --pane %2 --text "..."`
- `send-keys --pane %2 --keys C-m`
- `codex-state --pane %2`
- `codex-send --pane %2 --text "..." [--submit]`

Output should be short and machine-readable enough for an agent to use consistently. JSON is preferred for at least `list` and `codex-state`.

The helper should fail fast when:

- tmux is unavailable
- the pane id is missing where required
- the pane id does not exist

## File Layout

Planned additions:

- `skills/tmux/SKILL.md`
- `skills/tmux/scripts/tmux_helper.py`

Planned optional updates:

- `README.md` if bundled skill examples should mention `$tmux`

No installer changes should be necessary beyond the normal behavior of `install.py`, because it already copies any new directory under `skills/`.

## Testing Strategy

Keep verification light but real.

### Baseline pressure test

Before finalizing the skill, confirm the common failure mode without it:

- the agent can send text to a pane
- the agent can misread Codex prompt state
- the agent can over-capture other panes if not constrained

### Skill verification

Verify the new skill can guide or script these cases:

1. List panes without reading deeply.
2. Read only a specified pane.
3. Send text without submit.
4. Send submit key to a specified pane.
5. Detect likely Codex prompt state in another pane.
6. Refuse detailed read/send when no pane target is provided.

No heavy test harness is needed. A concise manual verification flow is enough for v1.

## Safety Notes

- Default to short captures.
- Do not make destructive tmux actions part of the core skill.
- Do not imply that a guessed pane target is safe enough.
- Treat pane output as potentially sensitive by default.

## Open Questions Resolved

- Control level: `safe-control`
- Codex-specific support: `yes`
- Targeting policy: `strict`
- Packaging: single skill plus helper script

## Implementation Outline

Implementation should happen in three narrow steps:

1. Add the helper script with the minimal subcommands needed for list, peek, send, and Codex-state checks.
2. Write `SKILL.md` around that helper, with strict target rules and Codex-aware playbooks.
3. Install the skill into the current Codex repo using the existing installer and verify discovery.

## Non-Goals

- Building a full tmux management framework
- Adding multi-pane automation strategies
- Supporting every tmux key or control path
- Solving GUI-level submit issues outside tmux semantics

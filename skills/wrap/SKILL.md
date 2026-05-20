---
name: wrap
description: สร้าง session retrospective, AI diary, lessons learned และบันทึก Kvasir memory ขึ้น GitHub สำหรับ repo private. ใช้เมื่อผู้ใช้พูดว่า wrap, retrospective, wrap up session, session summary, handoff หรือขอปิดงานพร้อมบันทึกความจำ
---

# $wrap

> "Reflect to grow, document to remember."

```text
$wrap              # Write memory, commit Kvasir/memory, push to GitHub
$wrap --detail     # Same, with full detailed template
$wrap --dig        # Reconstruct timeline from session logs, then save
$wrap --local      # Write memory only; no git commit
$wrap --no-push    # Write memory + commit; do not push
$wrap --deep       # Only mode allowed to use subagents; read DEEP.md
```

Default target is the current repository. In `Littar-Codex`, memory lives in `Kvasir/memory/**` and is intentionally committed because the repo is private.

## Non-Negotiables

- Do not spawn subagents or use Task tools unless mode is `--deep`.
- Do not commit anything outside `Kvasir/memory/**` during wrap.
- Do not push if the secret scan flags a likely secret.
- Do not rewrite history. Use follow-up commits for corrections.
- Thai output must use feminine particles only.

Invoking `$wrap` is approval to commit and push new/changed `Kvasir/memory/**` files after safety checks. It is not approval to commit unrelated repo work.

## Gather

Use PowerShell-compatible commands on Windows:

```powershell
Get-Date -Format "HH:mm K (dddd dd MMMM yyyy)"
git log --oneline -10
git diff --stat HEAD~5
git status --short --branch
```

Optional pulse context. Skip silently if missing:

```powershell
if (Test-Path Kvasir\data\pulse\project.json) { Get-Content -Raw Kvasir\data\pulse\project.json }
if (Test-Path Kvasir\data\pulse\heartbeat.json) { Get-Content -Raw Kvasir\data\pulse\heartbeat.json }
```

If pulse exists, weave it naturally into the retrospective rather than adding a dashboard.

## Write Memory

Create:

- Retrospective: `Kvasir/memory/retrospectives/YYYY-MM/DD/HH.MM_slug.md`
- Lesson: `Kvasir/memory/learnings/YYYY-MM-DD_slug.md`

Default retrospective includes:

- Session Summary
- Timeline
- Files Modified
- Key Commits / Pushes
- AI Diary: 150+ words, first person
- Honest Feedback: 100+ words, 3 friction points
- Lessons Learned
- Next Steps
- Metrics

Lesson includes:

- A concise reusable pattern
- Failure mode or trigger
- Concrete future rule
- Concepts/tags line

## Kvasir Sync

File-based memory is the working sync path. If a real `kvasir_learn` command or tool exists, call it after writing the lesson. If it does not exist, do not mark wrap as failed; record in the retrospective:

```text
File-based Kvasir memory sync completed. No callable kvasir_learn tool was available in this session.
```

## Secret Scan

Before staging memory, scan only the files about to be committed:

```powershell
git status --short Kvasir/memory
rg -n -i "(api[_-]?key|secret|token|password|passwd|bearer|cookie|session|private[_-]?key|BEGIN (RSA|OPENSSH|PRIVATE) KEY)" Kvasir/memory
```

If `rg` finds a real secret, stop. Redact the memory file first, then rerun the scan.

False positives such as prose saying "do not commit secrets" are allowed only after reading the exact match.

## Save To GitHub

Default `$wrap` save flow:

```powershell
git add Kvasir/memory
git diff --cached --check
git commit -m "wrap: record session memory YYYY-MM-DD"
git push origin HEAD
```

Rules:

- If there are no `Kvasir/memory` changes, say so and skip commit.
- If `git diff --cached --check` fails, fix whitespace and retry before commit.
- If unrelated files are dirty, leave them alone.
- If push fails because remote has new commits, stop and report; do not pull/rebase automatically during wrap unless the user asks.

Mode differences:

- `--local`: skip `git add`, commit, and push.
- `--no-push`: stage and commit `Kvasir/memory`, skip push.
- `--detail`: use the detailed template below.
- `--dig`: first reconstruct the timeline from available session logs or `$trace --dig`, then use `--detail`.

## Detail Template

```markdown
# Session Retrospective

**Session Date**: YYYY-MM-DD
**Start/End**: HH:MM - HH:MM GMT+7
**Duration**: ~X min
**Focus**: [description]
**Type**: [Feature | Bug Fix | Research | Refactoring | Skill Ops]

## Session Summary
## Timeline
## Files Modified
## Key Code Changes
## Architecture Decisions
## AI Diary
## What Went Well
## What Could Improve
## Blockers & Resolutions
## Honest Feedback
## Lessons Learned
## Kvasir Sync
## Next Steps
## Metrics
```

## Deep Mode

Only `$wrap --deep` may use subagents. Read `DEEP.md` in this skill directory before doing anything else.

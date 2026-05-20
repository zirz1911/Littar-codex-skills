---
name: littar-update-skills
description: Update and install all Littar Codex skills from the Littar-codex-skills repository. Use when the user asks to refresh, sync, pull, reinstall, or update local `.agents/skills` from `zirz1911/Littar-codex-skills`, including requests such as `$littar-update-skills`, "update all skills", "install all skills from the repo", or "sync Littar Codex skills".
---

# Littar Update Skills

## Overview

Refresh the local Littar Codex skill set from the GitHub source repository and install the bundled skills into a target Codex workspace. The default source checkout is `~/Project/Littar-codex-skills`; the default target is the current working directory.

## Workflow

1. Read the target repo instructions first when operating inside `Littar-Codex` (`CLAUDE.md`, then `AGENTS.md` if needed).
2. Use `scripts/update_littar_skills.py` from this skill.
3. Let the script clone the source repo if missing, pull it with `git pull --ff-only` when clean, and run the source repo's `install.py`.
4. Report the installed skill list and any dirty-repo blockers.

## Commands

Update all skills into the current workspace:

```bash
python3 .agents/skills/littar-update-skills/scripts/update_littar_skills.py
```

Update a specific target workspace:

```bash
python3 .agents/skills/littar-update-skills/scripts/update_littar_skills.py --target /home/paji/Littar-Codex
```

Install from an already-updated local checkout without pulling:

```bash
python3 .agents/skills/littar-update-skills/scripts/update_littar_skills.py --skip-pull
```

Use `--only <skill> [<skill> ...]` only when the user explicitly asks for selected skills. Otherwise install all bundled skills.

## Safety

- Do not use destructive git commands.
- If the source repository has uncommitted changes, stop and show `git status --short` instead of pulling.
- Use the source repo's installer as the only install path so `.agents/skills` and `skills-lock.json` stay consistent.

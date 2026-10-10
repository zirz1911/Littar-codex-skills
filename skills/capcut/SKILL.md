---
name: capcut
description: Edit CapCut desktop draft projects by project name and requested changes. Use when user asks to modify CapCut draft content/timeline directly in local folder C:/Users/pajipan/AppData/Local/CapCut/User Data/Projects/com.lveditor.draft, including trim video, trim silence, duration sync, track/segment edits, media path swaps, and metadata fixes.
---

# $capcut

Edit CapCut draft JSON directly, by project name and user intent.

## Scope

- Root drafts path: `C:/Users/pajipan/AppData/Local/CapCut/User Data/Projects/com.lveditor.draft`
- Target project by matching `draft_meta_info.json -> draft_name`
- Keep root files and timeline copies in sync

## Required Inputs

- Project name (example: `Google and safari 2`)
- Requested change (example: `trim silence`, `trim video`, `replace audio`, `fix duration`)

## Workflow

1. Resolve project directory.
2. Save the open draft and close CapCut yourself before writing. Use its normal close flow (or `CloseMainWindow()` on the main process), handle any save prompt, and verify all CapCut processes exit; closing the editor may only return to the home window, which must also be closed. Do not ask the user to do routine app opening or closing. Never force-terminate CapCut or edit while a save prompt or process remains; ask only if unsaved work cannot be saved safely.
3. Backup project files before edit.
4. Edit root files first:
- `draft_content.json`
- `template-2.tmp`
- `draft_meta_info.json`
5. Apply same logical updates to each timeline copy under `Timelines/<id>/` for matching files.
6. Validate JSON parse for all edited files.
7. Reopen CapCut yourself from its installed executable and verify timeline duration/material paths/track segments. If UI verification is unavailable, state that limit and revalidate the project files after reopening.

## Fast Commands

```bash
python skills/capcut/scripts/capcut_project_tool.py find --name "Google and safari 2"
python skills/capcut/scripts/capcut_project_tool.py backup --project "<absolute-project-dir>"
python skills/capcut/scripts/capcut_project_tool.py sync --project "<absolute-project-dir>" --file draft_content.json
python skills/capcut/scripts/capcut_project_tool.py sync --project "<absolute-project-dir>" --file template-2.tmp
python skills/capcut/scripts/capcut_project_tool.py validate --project "<absolute-project-dir>"
```

## Trim Rule (Critical)

- If user asks `ตัดวิดีโอ` or `ตัดส่วนที่เงียบ` (`cut-silence`): do timeline trim, not media replacement.
- Prefer adjusting segment timerange (`source_timerange`, `target_timerange`) and project `duration`.
- Keep `material_id` same whenever possible.
- Do not generate new media file unless user explicitly asks export/new file.

## Rules

- Never edit wrong project; confirm exact `draft_name` match first.
- Never skip backup.
- Never update only root or only timeline; update both sides.
- Never silently switch trim request into file-generation workflow.

## Verification Checklist

- `draft_content.json` and `template-2.tmp` parse as valid JSON in root and each timeline.
- `duration` consistent across edited files.
- segment timeranges align with final timeline length.
- audio/video material IDs still referenced by segments.
- CapCut opens draft without auto-repair prompt.

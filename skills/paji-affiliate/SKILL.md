---
name: paji-affiliate
description: Edit CapCut affiliate clips from per-clip media folders, using the local "SANMAX 1" draft as the project and editing-style reference. Keep the complete narration, cut only confirmed dead air, and create editable drafts without rendering unless requested.
---

# Paji-Affiliate

`$paji-affiliate` creates editable CapCut drafts for affiliate clips, one folder at a time. Duplicate **SANMAX 1** for each clip. Use its short-form pacing and occasional punch-ins as the reference; never edit the reference project or use a finished clip as the next template.

## Inputs and folder order

The user supplies one clip folder or a parent folder containing one subfolder per clip, plus any direction for product angle, pacing, narration, text, Favorite SFX, or generated image inserts. A `brief.md` or `brief.txt` inside a clip folder may give per-clip instructions; the user’s current message takes precedence.

- Keep each clip’s media separate. Process folders in the user’s stated order; otherwise sort by numeric prefix and then folder name.
- Within a clip, follow an explicit filename order or shot list. If neither exists, sort the video filenames naturally and match shots to the narration without mixing sibling folders.
- Identify the voiceover source. It may be a separate audio file or audio embedded in a video. If there are multiple plausible narrations and the choice is unclear, ask before editing.
- Keep source media in place because the CapCut draft references those files.

Run `python "<paji-affiliate skill directory>/scripts/inspect_inputs.py" --input "<folder>"` to inventory the clip queue and locate `SANMAX 1`. It is read-only. Resolve missing media, unclear narration, or a missing reference project before editing.

## SANMAX 1 editing profile

Use the reference as a guide to pacing and emphasis while keeping all content intelligible:

- Preserve its portrait 9:16 canvas and 30 fps setting (the reference canvas is 720×1280). Use brief shots, commonly around 1–4 seconds, and let the spoken phrase determine each cut. Occasional sub-second detail shots are fine when they do not remove speech.
- Match each visual to the product point being spoken. Use source shots in the requested filename order. Use occasional punch-ins for emphasis: the reference is mostly 1× scale, with some close-ups around 1.6×–2.3× and one very brief detail close-up. Keep the product or speaker in frame.
- Prefer straight cuts. The reference uses one short 0.4-second Fade Wipe; use a wipe sparingly when it supports a scene change.
- Keep the two full-length text tracks. Their wording may change to fit the current product and brief; both tracks must span the first through last video frame. Use `iannnnn-DOG Bold` (`iannnnn-DOG-Bold.ttf`) for all text. Retain the reference’s white or yellow fill with black outline unless the user asks for a different treatment.
- Keep added Overlay wording concise, at most five words unless the user sets another limit. Added Overlays are static: no entrance or exit animation, fade, slide, or pop. Keep the two full-length template tracks’ existing animation settings unless requested.
- Use about 2–3 quiet SFX accents on meaningful cuts or product moments when appropriate. Prefer sounds confirmed in CapCut Favorites, place them under the narration, and avoid masking speech. Never add Paper or paper-clipping sounds. The reference’s short keyboard sound is optional; do not add it unless the brief calls for it.
- When separate narration is used, keep it clear and aligned with the picture; the reference mutes source-video audio nearly completely. Preserve source audio when it is the requested narration instead of duplicating it.

Affiliate wording must stay within the user’s brief and the supplied product information. Do not invent features, discounts, results, or claims.

## Per-clip workflow

Repeat these steps sequentially for every clip folder until the queue is complete.

1. Inspect media, durations, orientation, narration, and brief. Transcribe only to understand the spoken content and map visuals; do not let speech recognition decide which content to keep.
2. Duplicate the exact local project named `SANMAX 1` into a unique project folder for this clip. Work directly in CapCut’s local projects folder by default: save and close CapCut yourself before file edits, copy the complete draft including its `video/` and `audio/` assets, assign fresh draft/timeline IDs, and update copied metadata and paths as required. Verify every media link in the duplicate. Never rename or modify `SANMAX 1`.
3. Build the edit around the complete narration. Cut only confirmed dead-air intervals detected in the source audio. Never use ASR/VAD speech detections as keep ranges; quiet or unrecognized speech must remain. Leave short handles around dead-air cuts, and keep all other source time. If a pause might contain speech, leave it in.
4. Cut and reframe video to the spoken product points using the SANMAX 1 pacing profile. Do not shorten a spoken phrase to fit a shot or target duration. If timing and complete speech conflict, keep the speech.
5. Update the two persistent text lines and add concise static Overlays as directed. Preserve both tracks and their styling, and make them end with the last video frame. Keep all text in the specified DOG Bold font.
6. Add only the requested or clearly fitting Favorite SFX. Use the reference’s sparse accents, keep them quieter than the narration, and do not add Paper effects.
7. Generate and insert small images only when the user asks. Keep them brief and relevant; do not bake text into generated images when editable CapCut text can be used.
8. Save and verify the editable duplicate on disk: timeline continuity, full narration, source links, 9:16 canvas, full-length text tracks, static added Overlays, and SFX. Use CapCut preview only when files and source media cannot verify a required detail or the user asks. Do not render or export unless explicitly requested.
9. Record the draft path, source folder, duration, text, SFX, and verification status. Move to the next folder only after this clip has a valid editable draft. Report exact blockers and continue only with independent folders whose inputs are clear.

## Safe project handling

- Resolve the projects root from `LOCALAPPDATA` and identify `SANMAX 1` by its `draft_meta_info.json` name. The editable draft is the deliverable; do not render by default.
- Before changing draft JSON, ensure the project is closed and not locked, and back up the new duplicate. Never force-close CapCut if it may contain unsaved user edits.
- Handle routine CapCut closing and reopening yourself without asking the user. Close through the normal app flow (or `CloseMainWindow()` on the main process), handle any save prompt, and verify every CapCut process exits before writing. If the editor returns to the home window, close that window normally too. Never force-terminate CapCut or risk unsaved user work; ask only if a save prompt cannot be handled safely. When an application check is needed, reopen from the installed executable and revalidate the draft files afterward.
- If editing JSON directly, update the matching `draft_content.json`, `template-2.tmp`, metadata, and active `Timelines/<id>/` copies. Preserve valid material IDs, track references, relative media, and microsecond timeranges. Keep the reference project’s embedded assets intact and verify the copied project resolves them.
- Use Computer Use only if the required property or operation cannot be handled or verified from project files and local media, or the user explicitly requests UI work.
- Preserve earlier projects, media, and backups. Choose a new name when one already exists.

## Completion report

Provide a compact per-folder summary with source folder, editable CapCut draft, duration, text, Favorite SFX, and any blocker. Mention an export only when the user asked for one. State only what was actually verified.

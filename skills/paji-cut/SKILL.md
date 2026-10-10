---
name: paji-cut
description: Edit one or more CapCut videos from the local "Template 1" draft. Use when the user gives a creative direction, voiceover, text, favourite sound effects, optional generated insert images, and a folder per clip. Duplicate the template for every clip, edit each duplicate sequentially, and keep the original untouched.
---

# Paji-Cut

`$paji-cut` creates editable CapCut drafts, one clip at a time. The source draft is **Template 1**. Never edit it in place, and never use a completed clip as the template for the next clip. Render or export only when the user explicitly asks.

## Inputs and folder convention

The user provides a media folder and any available brief: desired mood/pacing, voiceover, on-screen wording, requested favourite sounds or music, and whether to generate small image inserts. Use the supplied brief as the source of truth; infer ordinary edit choices from the media and voiceover.

- One clip: the selected folder contains that clip's video files and voiceover, or the user identifies the voiceover elsewhere.
- Several clips: each immediate child folder is one clip. Process in the user's stated order; otherwise sort by numeric prefix, then folder name. Do not mix files from sibling folders.
- A folder may contain `brief.md` or `brief.txt` for clip-specific directions. The user's current message overrides a file brief.
- Identify the exact voiceover for each clip. If multiple audio files could be the narration, use an explicit filename/brief; ask only when the choice cannot be inferred.
- Keep source media in place while editing because CapCut drafts reference their paths.

Run `python "<paji-cut skill directory>/scripts/inspect_inputs.py" --input "<folder>"` to inventory the queue and check `Template 1`. The script is read-only. Resolve missing media, ambiguous narration, or missing template before writing a draft.

## Per-clip workflow

Repeat these steps **sequentially for every folder** until the queue is complete.

1. **Read and plan.** Inspect all files, media durations/orientation, the voiceover, and the brief. Transcribe the narration when needed; use it as the script. Make a short shot map matching specific source shots to spoken phrases. Do not invent product features or claims.
2. **Duplicate first in the projects folder.** Save the open draft and close CapCut yourself before changing draft files, following the app lifecycle rule below. Locate the local draft whose `draft_meta_info.json` names it `Template 1`, then copy its whole project folder to a new, unique folder for this clip. Give the copy its own project and timeline IDs; update the copied metadata, paths, and matching timeline files so it is independent. Verify the copied name, IDs, and folder path before editing. Never rename or modify `Template 1`, and never use a prior completed clip as the source. Record the source folder and duplicate name in the batch log.
3. **Preserve template elements.** Keep both template text tracks and their wording/timing rules. Use the font family `iannnnn-DOG Bold` for every text element: both template lines, captions, overlays, and any text added with an insert. In draft files, use the matching `iannnnn-DOG-Bold.ttf` font asset. Preserve each element’s other styling (such as the title’s yellow fill and black outline, subtitle’s white fill and black outline, size, placement, and animation) unless the user asks to change it. Keep the title above the subtitle. Change wording only as directed; resize or reposition to fit the requested aspect ratio and safe area. Start both template tracks at time 0 and end them on the exact last video frame. Never delete either track or let either continue past the video.
4. **Keep content; cut only dead air.** Never use ASR/VAD speech detections as keep ranges: missed or quiet speech must not disappear. Start from the full source clips in filename order. Detect actual silence in the source audio, cut only confirmed dead-air intervals, and leave short handles around each cut so the preceding and following words remain intact. Keep all source time outside those silence cuts. If a quiet interval might contain speech, keep it. Use transcription only to check that words at edit boundaries remain complete. End after the last spoken phrase with a short natural tail; do not remove content to hit a target duration.
5. **Cut visuals to meaning.** Use the videos from this folder only. Match shots to the spoken words and cover the full cleaned narration. Read the active project’s canvas ratio, resolution, and frame rate first and honor the user’s settings. The established short-form profile is 9:16, 1080×1920, 30 fps unless the user requests otherwise. For portrait edits, reframe each shot to keep the character visible while cropping out any captured Windows title bar, taskbar, window border, or desktop area. Verify the crop at the beginning, middle, and end. Keep transitions simple; prefer straight cuts unless requested. No black gaps or missing-media frames.
6. **Add sound deliberately.** Use only CapCut **Yours → Favorites** sounds the user names or that clearly fit the brief. Verify Favorite status from available local CapCut data or, if that cannot establish it, in CapCut. Never add or reuse Paper/paper-clipping sound effects. For scene changes, use about 2–3 quiet swish/swoosh accents when they fit. Place them on actual cut points, lower them under the narration, and listen for masking or clipping. Follow the user’s sound instructions ahead of these defaults.
7. **Optional image inserts.** Generate images only when the user asks for them. Use supplied product references and the narration; save each generated image under the current clip's folder or a clearly named output subfolder. Insert briefly at the relevant spoken phrase, preserving the underlying video rhythm. Any new editable Overlay text is static: set its in-animation and out-animation to None, with no fade, slide, pop, or other entrance/exit effect. Keep existing template-track animation unchanged unless requested. Do not generate or insert an unsupported product claim. Use the image generation tool for requested generated images.
8. **Verify the editable draft.** Save the duplicate and check its JSON structure, media links, timeline duration, text spans, cut points, and SFX. Inspect source frames and audio around edits when needed. Open CapCut only if a property cannot be verified from project files and source media, or the user asks for an application check. Confirm every edit preserves complete words and phrases; portrait shots show no Windows title/taskbar; both locked text tracks span exactly from the first to last video frame; and no Paper SFX, dead air, blank frame, missing link, repair prompt, or accidental leftover audio remains. Do not render or export unless the user explicitly asks.
9. **Log and continue.** Record draft name/path, source folder, cleaned duration, chosen text, generated insert paths (if any), SFX used, and verification result. Start the next folder only after this one has a valid editable draft. If a clip is blocked, report the exact blocker and continue only with independent folders whose inputs are clear; return to the blocked clip when resolved.

## Safe CapCut draft handling

- Work in CapCut's local projects folder by default. The editable duplicate is the deliverable. Use Computer Use only when project files and source media cannot establish a required fact or action, or the user explicitly requests UI work; do not open CapCut merely to duplicate the template, import media, or edit the timeline.
- Before any direct draft JSON edit, close CapCut, back up the **duplicate**, and verify its `draft_meta_info.json` name and path. Never patch `Template 1`.
- Handle routine CapCut closing and reopening yourself without asking the user. Close through the normal app flow (or `CloseMainWindow()` on the main process), handle any save prompt, and verify every CapCut process exits before writing. If the editor returns to the home window, close that window normally too. Never force-terminate CapCut or risk unsaved user work; ask only if a save prompt cannot be handled safely. When an application check is needed, reopen from the installed executable and revalidate the draft files afterward.
- If editing JSON directly, update matching `draft_content.json`, `template-2.tmp`, and metadata in both the project root and its `Timelines/<id>/` copy. Maintain valid material IDs, source paths, track references, and microsecond timeranges. Verify structure and media paths on disk; use CapCut preview only for checks that cannot be resolved locally. Resolve the active CapCut path from `LOCALAPPDATA`.
- Preserve previous projects, media, backups, and exports. Choose a new name when one already exists.

## Completion report

Give a compact per-folder report with source folder, editable CapCut draft, duration, and any blocker. Mention an export only when the user requested one. State which two text lines and Favorite SFX were used for each completed clip. Report only what was actually verified.

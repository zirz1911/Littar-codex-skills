---
name: capcut-sub
description: Add editable, speech-synced, one-word-at-a-time subtitles to a local CapCut desktop draft by editing its project JSON. Use when the user names a CapCut project and asks for subtitles or exact word captions; not for exported-video-only captions.
---

# $capcut-sub

Add a separate text track to the named CapCut draft. Preserve existing tracks and media. This skill works on project files directly; do not use Computer use when the user prohibits it.

## Workflow

1. Resolve the **exact** `draft_meta_info.json -> draft_name`. Use `scripts/capcut_sub.py find --name "..."`; exclude `_backup` results. If profiles contain duplicate names, choose the project using the user's context rather than guessing.
2. Inspect `draft_content.json`: duration, primary video cuts, audible audio tracks, existing text style, active `Timelines/<draft id>/` copies, and material paths. `scripts/capcut_sub.py inspect --project "..."` gives a compact summary.
3. Extract the *edited timeline's* speech audio, including record voiceovers, with `extract --project "..." --out timeline.wav`. Check whether this draft has unusual speed effects, multiple speaking tracks, or missing media; adapt extraction when it does. Do not transcribe the uncut source and assign its times directly to the edited timeline.
4. Obtain timestamped ASR with `transcribe --audio timeline.wav --out raw.json --language th --initial-prompt "Codex, CapCut, ..."`. The helper needs `faster-whisper` and `numpy`; `wordify` also needs `pythainlp`. Use a local Python environment, for example `python -m pip install faster-whisper pythainlp`. The helper reads PCM WAV into NumPy before calling Whisper, avoiding PyAV WAV-version issues.
5. **Review every ASR phrase against the actual audio and available on-screen context.** Correct names, code/product terms, numbers, filler words, and missed speech. A second focused ASR pass can help ambiguous ranges. ASR alone does not prove verbatim accuracy. Save a JSON array of corrected phrases in the same order as `raw.json`; keep one element per raw segment. If segment boundaries need changing, edit the raw segment list and its word timings together.
6. Run `wordify --raw raw.json --corrected corrected.json --out captions.json --tsv captions.tsv`. Inspect the TSV for one spoken word per row, missed ranges, implausibly short/long timings, and boundary overlap. Adjust `captions.json` by ear where automatic alignment is off. Each caption object is `{"start": seconds, "end": seconds, "text": "word"}`.
7. Save the open draft and close CapCut yourself before writing; do not ask the user to perform routine app opening or closing. Use the app's normal close flow (or `CloseMainWindow()` on its main process), handle any save prompt, and verify all CapCut processes have exited. Closing the editor may return to CapCut's home window; close that window normally too. Never force-terminate a process or write while a save prompt or CapCut process remains. If unsaved work cannot be saved safely, ask the user only for that blocker. Run `apply --project "..." --name "exact draft name" --captions captions.json`. It makes a timestamped backup, adds a new word-caption track, and synchronizes root and active timeline `draft_content.json` / `template-2.tmp` plus metadata. It refuses an existing `Word subtitles` track so that reruns do not silently stack duplicates.
8. Run `validate --project "..."`; then reopen CapCut yourself from its installed executable and verify the draft displays and plays correctly when the permitted workflow allows that check. If UI verification is unavailable or prohibited, report that limit. Confirm CapCut did not overwrite the draft after reopening.

## Invariants

- Preserve the original tracks, media IDs, duration, other projects, and earlier backup/history files.
- Use a separate editable text segment and text material for **each** word; keep a single visible word at a time with timings on the edited timeline.
- Reuse an existing plain-text style in the target draft. If it has none, inspect a compatible local CapCut draft for a donor style and adapt it deliberately; do not fabricate an unverified CapCut schema.
- Back up before every project-file write. Keep root and active timeline copies identical. Validate all modified JSON, material references, segment ordering, and duration bounds.
- State transcription uncertainty honestly. Exact wording requires listening and correcting ASR, especially Thai speech mixed with English product names.

`scripts/capcut_sub.py --help` lists the command options. The helper handles the standard single-primary-video-track draft shape used here; inspect and adapt unusual drafts before applying it.

---
name: capcut-affiliate
description: Edit an existing CapCut affiliate draft using either the saved Ascen Paji 1 default style or a user-named CapCut draft as the style reference. Build an editable, speech-aligned product video from the target's own footage and add SFX from CapCut Favorites. Save, close, and reopen CapCut yourself when direct draft editing is needed.
---

# $capcut-affiliate

Use this skill when the user names an affiliate-video draft to edit. The **target** is the deliverable. Style can come from this skill's saved default profile or a separate user-named CapCut draft. Do not export unless requested.

## Choose the style

Unless the user already chose a style source in the current request, ask this two-option question before editing:

> ต้องการใช้สไตล์แบบไหนคะ?
> 1. ใช้ค่าพื้นฐานของสกิล (สไตล์สายชาร์จ Ascen Paji 1)
> 2. ใช้ตามโปรเจคที่ต้องการ (ระบุชื่อโปรเจคต้นแบบ)

- For option 1, read `references/ascen-default-style.md` and apply that profile **without requiring the original Ascen project**. Do not ask for a reference project or treat the target's empty Main Track as evidence that footage is missing.
- For option 2, get the exact reference project name if it was not supplied. The reference supplies pacing, typography, placement, canvas, and sound style; its product footage and claims do not belong in the target. If the named reference is unavailable, ask whether to use the saved default or provide another name.

## Inputs and project discovery

- Identify the target and, only for option 2, the reference by the names the user gives. Resolve the CapCut projects root from `$env:LOCALAPPDATA\CapCut\User Data\Projects\com.lveditor.draft`. Inspect each candidate's `draft_meta_info.json` and match its `draft_name`; folder names can differ. If names are ambiguous, inspect the project covers and contents before editing.
- Run `python "<skill directory>/scripts/inspect_imported_media.py" --name "<target draft name>"` before deciding footage is missing. CapCut can show imported clips in the Media bin while the Main Track and `draft_content.json -> materials.videos` are empty. The imported clips may be listed only under `draft_meta_info.json -> draft_materials[].value[] -> file_Path`, with source files outside the draft folder. Check those paths and the draft's `video/` directory. A reference in the Media bin is usable when its source file exists; it does not need to be on the timeline already.
- Inspect the target's current tracks, narration, imported footage, embedded `video/` and `audio/` assets, and any supplied media or shot order. A related source draft may contain the target's product footage, but verify its identity by media content and user context before using it. Never silently use the reference project's unrelated product shots. Ask for media only after checking the import inventory and confirming that the referenced source files are missing or inaccessible.
- For option 2, inspect the reference's active timeline, frame size, cuts, text, effects, SFX, and audio levels. Derive a style profile from that draft. For option 1, use the saved profile; do not assume its original duration or shot count fits every narration.
- Read the user's product brief or supplied copy. If wording is unclear, transcribe the narration for timing and ask about only the uncertain claims or names that would affect the edit. Do not invent features, prices, discounts, or results.

## Edit the target

1. Map the complete narration into spoken points, then select target footage for each point. Let speech set the total duration. Keep every spoken phrase and short natural pauses; speech recognition or silence detection alone must not remove content.
2. Make short, purposeful shots and straight cuts with pacing comparable to the chosen style. Reframe for its portrait canvas when appropriate, keeping the product in view. Use its transitions or punch-ins only where they improve the current footage.
3. Adapt the chosen style's editable text treatment to the current product. When it has persistent title tracks, retain their styling and extend the adapted target text through the last video frame. For the saved default style, **both persistent text tracks must have the 0.5 s `Type 1` typing-in entrance**; font and position alone do not reproduce that animation. Use brief additional editable overlays only where they clarify narration. Check spelling and avoid covering the product.
4. Keep the target narration as the primary audio. Mute or lower source-footage sound if it duplicates or masks the narration. Plan about **3–5 SFX cues per clip**, including the opener, based on visible actions rather than placing a sound on every cut. For the saved default style, always open with the keyboard sound; use a swish or swoosh to cut into a product shot and a pop when the product is revealed or emphasized. Choose the remaining cues only where they fit. For a named reference, follow its opening sound unless the user asks for the Ascen keyboard opener. Get the effects from **CapCut Sounds / Sound effects / Favorites** as described below. Mix below narration and audition the transitions and product reveals when playback is available.
5. Keep the result as an editable CapCut draft. Preserve valid media paths, material IDs, track IDs, source ranges, and microsecond target ranges. Generate new IDs for copied materials or segments where needed; do not change any reference draft.

## Get SFX from CapCut

- CapCut's Favorites are the source of the sounds. They do **not** have to be in the target draft's Media bin or timeline first. An empty SFX track means the edit is missing cues, not that CapCut lacks the sounds. Search Favorites by the names in `references/ascen-default-style.md`; select suitable keyboard, swish/swoosh, and pop sounds and place them at the planned moments.
- For the saved default style, use the **required SFX workflow below**. `references/capcut-favorite-sfx.json` contains reusable CapCut Favorite material templates, so the original Ascen draft is not needed. Its cache paths are local CapCut resources, not files to request from the user.
- If a template's cache file is absent, add the sound through CapCut Favorites in the app. CapCut can obtain its own copy. Complete the SFX placement in the app and then run the verification command below; do not silently drop the SFX or ask the user to upload an effect available in CapCut.

### Required SFX workflow for the saved default style

1. After choosing the video cuts, write a JSON plan with 3–5 cues. Use `keyboard` at 0 seconds, `swish` or `large_whoosh` across a product-entry cut, and `pop` or `low_pop` on a product reveal. Available keys: `keyboard`, `keyboard_alternative`, `swish`, `wind_swipe`, `large_whoosh`, `pop`, `low_pop`. Example format: `[{"sound":"keyboard","start_seconds":0,"volume":0.32},{"sound":"swish","start_seconds":1.6,"volume":0.28},{"sound":"pop","start_seconds":5.5,"volume":0.30}]`. Choose actual times from the current edit, not this example.
2. Run `python "<skill directory>/scripts/capcut_sfx.py" plan --name "<target draft name>" --plan "<absolute plan.json>"`. Fix any missing resource or invalid cue reported. The plan is read-only.
3. Save and close CapCut yourself as described below. Run the same command with `apply` in place of `plan` to back up the target and insert editable SFX tracks. If a cache resource is missing, use CapCut Favorites in the app for the SFX instead.
4. Reopen CapCut and run `python "<skill directory>/scripts/capcut_sfx.py" verify --name "<target draft name>"`. **A nonzero exit or `valid: false` means the edit is incomplete.** Inspect the new tracks and play the opening, product-entry, and reveal cues when UI playback is available. Correct the edit before reporting completion.

For a user-named style reference, adapt its sounds and use CapCut Favorites as needed. Verify 3–5 intentional, audible SFX on the target timeline. Do not report a completed affiliate edit with zero SFX or phrase their absence as an optional limitation; report the specific CapCut access blocker and continue once it is resolved.

### Required typing-in workflow for the saved default style

1. After creating the two persistent text tracks, run `python "<skill directory>/scripts/capcut_typing.py" verify --name "<target draft name>"`. The check looks for a `Type 1` **In** animation of 500,000 microseconds on **each text segment's `extra_material_refs`**, backed by `materials.material_animations`. A text material's font or full-length target range does not prove typing-in is present.
2. If verification fails because the animations are absent, run the same command with `plan` in place of `verify`. Save and close CapCut, then run it with `apply` to back up the draft and insert the saved `references/typing-in-animation.json` template with fresh material IDs. If the effect cache is missing or another animation is already present, set `Animation > In > Type 1` to 0.5 s on both text clips in CapCut instead, then save.
3. Reopen CapCut, run the `verify` command again, and preview the first half-second when UI playback is available. **A nonzero exit or `valid: false` means the default-style edit is incomplete.** Do not claim it matches Ascen while the text appears fully at frame zero.

## Save, close, back up, and reopen CapCut

- Inspect first. Before writing draft files, save and close CapCut yourself through its normal UI flow, or use `CloseMainWindow()` on the main process. A closed editor may return to CapCut Home; close that normally too. Handle a save prompt and confirm all CapCut processes have exited. Do not force-terminate or write while an unsaved prompt or process remains. Ask the user only if the open work cannot be saved and closed safely.
- Back up the target's root `draft_content.json`, `template-2.tmp`, `draft_meta_info.json`, cover, and matching active `Timelines/<id>/` files before changes. Keep original media and previous backups. Do not overwrite a reference draft.
- Write root and active timeline copies consistently. Update duration, metadata, and cover when affected. Prefer references to existing target media; preserve files at their referenced paths.
- Validate JSON, every segment's material reference and media path (including every SFX file), nonnegative source ranges, contiguous primary video to the narration end, audio alignment, full-length persistent text, approximately 3–5 intentional SFX cues, and matching root/timeline copies. Run both the SFX and typing-in verification commands after reopening CapCut for the saved default style; disk validation before launch alone is insufficient.
- Reopen CapCut yourself from the installed executable under `$env:LOCALAPPDATA\CapCut\Apps\CapCut.exe` (or locate the installed executable). Inspect the target in the app when available, including playback and text placement. Revalidate files after launch so an app rewrite is caught. If app inspection is unavailable, report exactly what was checked on disk.

## Completion

Report the target draft name and path, style source (saved default or named reference), duration and cut count, adapted text and SFX, backup path, and verification performed. State any missing media or UI verification limit plainly. Do not claim a playback check that did not happen.

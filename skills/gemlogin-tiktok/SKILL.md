---
name: gemlogin-tiktok
description: TikTok-specific GemLogin workflow knowledge for DB-first surgery, live selector verification, and stable routing in workflows such as `[TikTok] Like comment share`, `[TikTok] Like comment share - No Text File`, and `[TikTok] Upload Video`. Use when Codex needs to patch, explain, extend, or debug TikTok automation flows in GemLogin, especially for comment input, share modal branches, repost/copy behavior, post confirmation, latest-link capture, or file-input to string-input migration.
---

# Gemlogin Tiktok

Use this skill when task is TikTok-domain workflow work, not generic GemLogin editing.

Pair it with:
- `$gemlogin-edit` for actual DB write, backup, reload, and graph patch workflow
- `$gemlogin` when live profile, script listing, or profile runtime state matters

## Quick Checks

Before patching, identify which class of TikTok workflow you have:
- `[TikTok] Like comment share` or variants: comment box, share modal, comment-link capture
- `[TikTok] Warm-up Feed`: feed loop, weighted actions, ads skip, next-card scroll
- `[TikTok] Upload Video`: upload form, caption clear/fill, `Post now` confirm, latest video URL capture

If user points to active browser state like `VEO 2`, inspect live tab/profile first instead of patching blind.

If user asks for xpath or selector reliability, verify against live DOM. Do not trust old workflow JSON alone.

## Core Rules

1. Read whole graph first: upstream variable setters, branch handles, and downstream targets.
2. Prefer built-in blocks over JS when behavior is simple and stable.
3. Keep one submit source of truth. If `press-key Enter` submits comment, JS submit path must not also submit.
4. Treat modal state as explicit workflow state. `Copy`, `Repost`, `Post`, and `Post now` are separate states.
5. After DB patch, reload GemLogin UI and read back real workflow shape before trusting result.
6. In feed loops, clear stale panels before next action or toggle-style buttons can invert state instead of opening UI.

## Comment Workflow Pattern

Use this for `Like comment share` style flows.

- Stable comment input path:
  - open comments
  - fill contenteditable comment box
  - submit with `press-key Enter`
- For contenteditable fields, fallback pattern is:
  - focus
  - select all
  - clear
  - fill
- Keep JS typing only as fallback when form block fails.
- Do not leave duplicate JS submit logic active beside `press-key Enter`.

## Comment Link Capture Pattern

Stable capture path after comment submit:
- click comment timestamp or time label
- use `clipboard` block with `type: "get"`
- append clipboard result into output file with `command` or `file-action`

Prefer `file-action` when only writing resolved variable.
Use `command` when user explicitly wants PowerShell behavior or custom file handling.

## Share Modal Pattern

TikTok share modal is stateful. Do not model it as one click.

- `Copy` can close modal.
- If later step needs `Repost`, workflow must reopen share modal first.
- Real branch shape should model:
  - open share
  - choose copy or repost
  - if copy closes modal, reopen before repost path
- Route handles must match condition ids exactly:
  - `share-route-node-output-cond-share-copy`
  - `share-route-node-output-cond-share-repost`

When user asks to extend share flow, inspect live DOM for `data-e2e` or equivalent selectors first.

## Warm-up Feed Pattern

Use this for `[TikTok] Warm-up Feed` style workflows.

- Trigger parameters used:
  - `max_clips`
  - `target_watch_minutes`
  - `like_percent`
  - `comment_percent`
  - `share_percent`
  - `repost_percent`
  - `watch_time_min`
  - `watch_time_max`
  - `comment_pool`
- Stop logic:
  - if both clip and minute limits are set, stop on whichever comes first
  - if both are `0`, fallback to safe default clip limit instead of infinite run
- Stable graph shape:
  - `open-url -> wait-feed -> loop-data -> choose-action -> watch-delay -> route-action`
  - every action branch returns to `scroll -> scroll-pause -> loop-breakpoint`
- Prefer note blocks to split:
  - `SETUP + DECISION`
  - `LIKE`
  - `COMMENT`
  - `SHARE / REPOST`
  - `SCROLL + LOOP`

## Warm-up Feed Selectors

Live-verified from `VEO 2` TikTok feed:

- Like:
  - `button[aria-label^="Like video"][aria-pressed="false"]`
- Comment button:
  - `button[aria-label^="Read or add comments"]`
- Share button:
  - `button[aria-label^="Share video"]`
- Comment input:
  - `[data-e2e="comment-input"]`
  - `[data-e2e="comment-text"]`
  - `[role="textbox"][contenteditable="true"]`
- Comment submit:
  - `//*[@data-e2e='comment-post' and not(@disabled)]`
- Share copy:
  - `((//*[@data-e2e='share-copy']//*[@tabindex='0'])[1] | (//*[@data-e2e='share-copy'])[1])[1]`
- Share repost:
  - `((//*[@data-e2e='share-repost']//*[@tabindex='0'])[1] | (//*[@data-e2e='share-repost'])[1])[1]`

## Warm-up Feed Runtime Rules

- Ads skip markers:
  - `[data-e2e="ad-tag"]`
  - `[data-e2e="ttam-ads-cta"]`
  - text `Sponsored`
- If active card is ad:
  - set action to `scroll`
  - do not like, comment, share, or repost
- If clip has no comment button:
  - skip comment path and scroll next
- After comment submit:
  - close comment panel before next video
  - on next loop, cleanup stale panel first if needed so comment button does not toggle closed state
- If `forms` fill fails because panel closed or lost focus:
  - reopen comments once
  - reuse same picked comment
  - if second fill fails, close panel and move on

## Feed Scroll Pattern

For TikTok feed, `element-scroll` can move only tiny distance and fail to advance video.

- Better pattern:
  - find active `data-e2e="recommend-list-item-container"` card near viewport center
  - read its `data-scroll-index`
  - scroll next card into view
- Stable JS behavior:
  - `nextCard.scrollIntoView({ block: 'start', behavior: 'instant' })`
  - fallback `window.scrollBy(0, window.innerHeight)`
- Validate on live feed:
  - active card index should change, not only page `scrollY`

## Upload Publish Pattern

Use this for `[TikTok] Upload Video`.

- First `Post` click is not always final publish.
- TikTok can show confirm modal with `Continue to post?` and button `Post now`.
- Stable logic:
  - click `Post`
  - wait
  - detect confirm state
  - route `confirm` -> click `Post now`
  - route `done` -> continue

Avoid blind double-post clicking.

## Latest Video Link Capture Pattern

Stable post-publish path:
- open `https://www.tiktok.com/tiktokstudio/content`
- wait for list
- read first `a[href*="/video/"]`
- store to variable like `latest_video_url`
- append to output file with `file-action`

Prefer this over scraping transient upload dialogs.

## File Input To String Input Migration

Use this when workflow should stop depending on separate `.txt` inputs.

- Change manual trigger params in both places:
  - `script.trigger.parameters`
  - `trigger-node.data.parameters`
- Keep output file params as `filepath` when user still wants saved links.
- Replace old `read-file-text` nodes with `javascript-code` loaders that populate same downstream variables.

Safe migration pattern from `[TikTok] Like comment share - No Text File`:
- `comment_text` -> loader sets `comment_line`
- `link_url` -> loader sets `raw_links`
- one-shot guard like `link_input_consumed` prevents infinite re-read of same string

Important:
- old list workflows often loop back into reader node on `skip` or `next`
- after moving to single string input, retarget branch to `end-node` or make reader one-shot
- otherwise same URL can loop forever

## Conditions And Routing

For TikTok workflows, explain `conditions` blocks in this order:
- upstream node that sets state variable
- condition definitions inside block
- `sourceHandle` mapping like `output-cond-valid`
- target nodes and edge labels

Short edge labels help a lot in fallback-heavy TikTok graphs:
- `Open URL`
- `Invalid link`
- `Post now`
- `Reopen share`

## Good Trigger Phrases

Use this skill when user asks things like:
- `edit TikTok workflow in db`
- `find stable TikTok xpath`
- `add Copy/Repost branch`
- `change TikTok input from text file to string`
- `make TikTok publish handle Post now`
- `save TikTok video/comment link into file`

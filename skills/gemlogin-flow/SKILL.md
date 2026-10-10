---
name: gemlogin-flow
description: Operate Google Flow through GemLogin profiles. Use when the task is specifically about labs.google/fx Flow pages, collecting XPath selectors, generating images, downloading outputs, or patching GemLogin workflows for Flow.
---

# Gemlogin Flow

Use this skill when the target is Google Flow inside a GemLogin browser profile.

This is a narrow companion to `$gemlogin` and `$gemlogin-edit`:
- `$gemlogin`: connect to the running GemLogin app, inspect profiles, and get the remote debugging address.
- `$gemlogin-flow`: work inside Google Flow pages, collect stable XPath selectors, test generation/download flows, and document Flow-specific behavior.
- `$gemlogin-edit`: patch GemLogin workflow JSON in `db.db`.

## Scope

Use this skill for tasks like:
- Find the currently open Flow page in a GemLogin profile.
- Attach Selenium or Playwright to the active profile via `debuggerAddress`.
- Collect XPath selectors for Flow controls.
- Trigger image generation and wait for output.
- Download generated images and choose `1K`.
- Design or verify Flow-specific workflow logic before patching it into GemLogin.

## Preferred Stack

For Flow work, prefer this order:

1. Use `$gemlogin` MCP tools to identify or start the profile.
2. Attach Selenium to the existing Chromium session through `debuggerAddress`.
3. Read DOM directly and derive XPath from live elements.
4. Use built-in GemLogin blocks for workflow steps where possible.
5. Use JavaScript only for Flow behaviors that built-in blocks cannot express cleanly.

Do not use raw CDP websocket calls as the primary path when Selenium attachment works. Flow sessions may reject websocket origins directly.

## Flow Rules

1. Prefer visible, clickable wrapper elements over inner `img` tags.
   - For image cards, clicking the wrapping `a` is more stable than clicking the nested `img`.
2. When prompt input is a Slate editor, use real typing events.
   - `send_keys` is preferred over setting `innerHTML`.
3. For generation waits, do not rely on progress text unless it is actually present.
   - Flow often does not expose a stable visible progress label.
4. Prefer media-state waiting for image generation.
   - Snapshot current generated media count and src list before clicking Generate.
   - After Generate, wait until count increases or the src signature changes.
   - Add a short buffer before clicking a fresh result card.
5. For download menus, wait for the menu option itself.
   - Do not assume the `1K` option is available immediately after clicking download.

## Known Stable Selectors From This Repo Session

These were verified on `https://labs.google/fx/th/tools/flow` during this session and should be treated as useful defaults, not eternal truth.

- Prompt editor:
  - `/html[1]/body[1]/div[1]/div[1]/div[5]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]`
- Generate button:
  - `/html[1]/body[1]/div[1]/div[1]/div[5]/div[1]/div[1]/div[1]/div[1]/div[2]/div[2]/button[2]`
- First image card anchor:
  - `/html[1]/body[1]/div[1]/div[1]/div[4]/div[2]/div[1]/div[1]/div[1]/div[2]/div[1]/div[1]/div[1]/div[1]/div[1]/span[1]/div[1]/div[1]/div[1]/div[1]/span[1]/div[1]/a[1]`
- Download button in viewer:
  - `/html[1]/body[1]/div[1]/div[1]/div[1]/div[2]/div[1]/div[1]/div[4]/button[2]`
- Download `1K` option:
  - `/html[1]/body[1]/div[3]/div[1]/button[1]`
- Media row container:
  - `/html[1]/body[1]/div[1]/div[1]/div[4]/div[2]/div[1]/div[1]/div[1]/div[2]/div[1]/div[1]`

## Working Pattern

Typical Flow automation loop:

1. Confirm GemLogin local API is up.
2. Get the target profile and `remote_debugging_address`.
3. Attach Selenium to the existing profile.
4. Inspect the current Flow page.
5. Collect or verify XPath selectors from live DOM.
6. Run the user action.
7. If generation is involved, wait on media-state change.
8. Save important selectors or observations into `active/*.json`.
9. If the user wants a reusable GemLogin workflow, switch to `$gemlogin-edit`.

## Workflow Guidance

When turning Flow actions into GemLogin workflows:
- Prefer built-in blocks for:
  - `open-url`
  - `event-click`
  - `element-exists`
  - `forms`
- Use JS blocks for:
  - media snapshot before generate
  - waiting for generated media count/src changes
  - other Flow-only state detection where no stable DOM text exists

If a click fails with `Element is not visible`:
- add a real wait node before the click
- add a short buffer after state change
- click the wrapper anchor/button instead of a nested visual child

## Safety

- Never expose cookies, tokens, or session secrets from the Flow page.
- Do not store account secrets in repo files.
- If editing GemLogin workflows, back up `db.db` first and reload GemLogin after writing.

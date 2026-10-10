---
name: gemlogin-browser
description: Open a user-selected GemLogin browser profile, navigate to a requested website, perform a described browser behavior, and capture verified XPath/CSS/semantic selectors through CDP. Use when the user asks to inspect or operate a website inside a GemLogin profile, collect selectors, or turn a live browser interaction into reusable selector evidence.
---

# GemLogin Browser

Operate one GemLogin profile at a time and leave a selector artifact that can be reused by workflows.

This skill complements:

- `$gemlogin` for GemLogin API status, profile lookup, start, and stop.
- `$gemlogin-edit` only when the user explicitly asks to write a GemLogin workflow into `db.db`.
- Domain skills such as `$gemlogin-flow` or `$gemlogin-tiktok` when the website has a dedicated workflow.

## Required input

Resolve these from the user's request before acting:

- profile: exact profile id, name, or group
- website: URL or current page to inspect
- behavior: ordered actions such as open, click, fill, press, scroll, wait, or read
- capture: named targets whose selectors should be recorded

If profile or website is ambiguous, inspect available state and ask only when an exact target still cannot be determined.

## Runtime

1. Use `$gemlogin` to confirm the local API and resolve the exact profile. Do not fuzzy-match a destructive or state-changing target.
2. Start the profile with `gemlogin_start_profile` and retain the returned `remote_debugging_address`.
3. Attach Playwright or Selenium to that existing Chromium session through CDP. Prefer Playwright/Selenium APIs for navigation, typing, clicking, and waiting; use raw CDP `Runtime.evaluate` for DOM inspection and selector evidence.
4. Navigate to the requested URL unless the user explicitly asks to inspect the current tab. Confirm the final URL and page title.
5. Execute behavior in order. After every state-changing action, wait for the resulting visible state rather than relying on a fixed sleep alone.
6. Capture each named target from the live DOM. Run `scripts/capture_selectors.py` with the active CDP address when deterministic extraction is useful.
7. Verify every candidate selector against the live page: match count, visibility, enabled/clickable state where relevant, and whether it identifies the intended element. Prefer a selector with exactly one match.
8. Save evidence as `active/gemlogin-browser-<site>-<date>.json`. Never include cookies, tokens, localStorage, session values, passwords, or full page dumps.
9. Stop the profile with `gemlogin_stop_profile` unless the user explicitly asks to keep it open.

## Selector priority

Prefer selectors in this order:

1. `data-testid` or another test-oriented stable attribute
2. `aria-label`, accessible role/name, or semantic attributes
3. stable `name`, `placeholder`, `href`, or `data-*` attributes
4. text XPath using `contains(., ...)`, not `contains(text(), ...)`
5. scoped CSS/XPath with a stable ancestor
6. indexed or absolute XPath only as a documented fallback

Before recording XPath, inspect the actual element tag, role, accessible name, and stable attributes through CDP. Do not use React-generated ids or volatile CSS classes as the primary selector. Scope selectors to the visible dialog/card/container when duplicate controls exist.

## Artifact shape

Use this compact shape for saved evidence:

```json
{
  "profile": {"id": "3", "name": "Facebook 2"},
  "url": "https://example.com/page",
  "title": "Page title",
  "captured_at": "2026-07-14T00:00:00Z",
  "behavior": ["open menu", "click Create post"],
  "selectors": [
    {
      "name": "create-post",
      "xpath": "//button[@aria-label='Create post']",
      "css": "button[aria-label='Create post']",
      "tag": "button",
      "role": "button",
      "aria_label": "Create post",
      "text": "Create post",
      "match_count": 1,
      "visible": true,
      "enabled": true,
      "verified": true
    }
  ]
}
```

The reusable helper is `scripts/capture_selectors.py`. Run it with Python and a live CDP address, for example:

```bash
python3 scripts/capture_selectors.py \
  --debugger-address 127.0.0.1:9222 \
  --name create-post \
  --aria-label "Create post" \
  --output active/create-post.json
```

The helper requires `websocket-client`; use Playwright/Selenium directly when that package is unavailable.

## Failure handling

- If GemLogin API is unavailable, stop and report that GemLogin must be opened.
- If CDP has no page target, report the profile/debug address and do not guess a different profile.
- If a selector matches zero or multiple elements, keep it as unverified and record the reason; do not silently promote it.
- If a SPA changes the DOM after an action, recapture from the current state.
- If the page exposes fingerprint or login problems, record the observed state separately from selector failure. Do not expose account data.

## Scope

This skill captures and verifies live browser behavior. It does not edit GemLogin's SQLite database or create workflows unless the user separately requests `$gemlogin-edit`.

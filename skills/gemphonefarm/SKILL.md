---
name: gemphonefarm
description: Run, register, and use the GemPhoneFarm MCP server from a local gemphonefarm-mcp clone on macOS or Windows. Use when the user asks to connect Codex or another MCP client to GemPhoneFarm; start or refresh the MCP server; register it with `codex mcp add`; build, install, or troubleshoot GemPhoneFarm workflows; inspect scripts; or verify the local GemPhoneFarm API and device automation stack.
---

# Gemphonefarm

Use this skill to work with a local `gemphonefarm-mcp` checkout.

Workflow authoring rules for this repo:
- Set workflow `author` to the agent name currently in use, not `QCCAP-FARM`.
- Use `GEMPHONEFARM_WORKFLOW_AUTHOR` for a machine/client default when you want the builder to stamp one agent name automatically.
- Set workflow `name` exactly to the user-facing workflow name the user asked for, usually including the platform first, for example `TikTok - Engage`, `Facebook - Warmup`, or `YouTube - Comment`.
- Do not silently rename workflows to an internal convention if the user already gave a platform-specific name.

Do not assume one path. First confirm where the repo exists on the current machine.

Typical locations:
- macOS: `/Users/<you>/Desktop/.../gemphonefarm-mcp`
- Windows: `C:\Users\<you>\Desktop\...\gemphonefarm-mcp`

GemPhoneFarm desktop app must be open first so the local API responds on `http://localhost:1256`.

## Quick Checks

Verify the app API and repo before changing MCP config:

```bash
curl -fsS http://localhost:1256/scripts >/dev/null
test -f /path/to/gemphonefarm-mcp/pyproject.toml
```

Windows PowerShell:

```powershell
Invoke-RestMethod http://localhost:1256/scripts | Out-Null
Test-Path C:\path\to\gemphonefarm-mcp\pyproject.toml
```

If `localhost:1256` refuses the connection, open GemPhoneFarm and wait for the UI/API to finish starting.

## Install Or Refresh

Install from the local repo so the MCP entrypoint is current:

```bash
python -m pip install -e /path/to/gemphonefarm-mcp
```

Smoke-run the server only through an MCP client or inspector because it speaks stdio:

```bash
python -m gemphonefarm_mcp.server
```

Stop it with `Ctrl+C` if started manually.

## Register With Codex

```bash
codex mcp add gemphonefarm -- /absolute/path/to/python -m gemphonefarm_mcp.server
codex mcp list
```

If startup is slow:

```bash
codex mcp add gemphonefarm \
  --env GEMPHONEFARM_TIMEOUT=120 \
  -- /absolute/path/to/python -m gemphonefarm_mcp.server
```

## Register With Codex

```bash
Codex mcp add gemphonefarm -- /absolute/path/to/python -m gemphonefarm_mcp.server
Codex mcp list
```

If the client still cannot see tools after registration, restart that client.

## Runtime Checks

```bash
ps -ef | rg 'gemphonefarm_mcp.server'
curl -fsS http://localhost:1256/scripts | head
curl -fsS http://127.0.0.1:50000/dump/hierarchy
```

> **API path note**: `GET /scripts` lists all scripts (no `/api/` prefix). `GET /scripts/{id}` returns 404 — filter the list response by name or id instead. `POST /scripts` creates; `DELETE /api/scripts/{id}` deletes. This path asymmetry matches GemPhoneFarm's Express route registration.

The hierarchy endpoint only works when `atx-agent` is up and its port forward exists for the target device.

## Tool Map

Once connected, prefer the MCP tools instead of raw shell:

- device listing and grouping tools for fleet state
- workflow build/install tools for GemPhoneFarm scripts
- bundled `All Block` template tools for real block discovery and install
- ADB-backed tap, swipe, key, type, shell, screenshot tools
- hierarchy dump tools for XPath capture
- For throwaway Python helpers, prefer inline `python - <<'PY'`. If a file is unavoidable, create it as a temp file and delete it immediately after execution.

Relevant bundled-template tools/resources:
- `gemphonefarm_get_all_block_template`
- `gemphonefarm_install_all_block_template` (auto-reloads UI after install)
- `gemphonefarm_list_workflow_blocks`
- `gemphonefarm://blocks`
- `gemphonefarm://templates/all-block`

## Troubleshooting

- `connection refused :1256`: GemPhoneFarm app is not open or API is not ready.
- import failure or missing command: rerun editable install with the intended interpreter, then restart the MCP client.
- MCP registered but tools missing: restart Codex or Codex.
- hierarchy dump fails: open scrcpy/device view first or restart `atx-agent` on device.
- workflow visible in API but stale in UI: reopen GemPhoneFarm script list or restart the app.

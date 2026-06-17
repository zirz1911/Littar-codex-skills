---
name: gemlogin
description: Run, register, and use the GemLogin MCP server from a local gemlogin-mcp clone on Windows or macOS. Use when the user asks to connect Codex, Claude Code, Cursor, or another MCP client to GemLogin; list, start, stop, warm, or automate GemLogin browser profiles; get a CDP remote debugging URL; run GemLogin local scripts; or troubleshoot GemLogin MCP/local API issues.
---

# Gemlogin

Use this skill to work with a local `gemlogin-mcp` checkout.

Typical repo locations seen so far:
- Windows: `E:\Projects\gemlogin-mcp`
- macOS: `/Users/pajipan/Desktop/Paji/project/gemlogin-mcp`

Do not hardcode one path blindly. First confirm where the repo exists on the current machine.

GemLogin itself must be running first. The MCP server is a thin stdio wrapper around GemLogin's local REST API, defaulting to `http://localhost:1010`.

## Quick Checks

Before changing MCP client config, verify the local app and repo:

```bash
curl -fsS http://localhost:1010/api/status
test -f /path/to/gemlogin-mcp/pyproject.toml
```

Windows PowerShell equivalent:

```powershell
Invoke-RestMethod http://localhost:1010/api/status
Test-Path E:\Projects\gemlogin-mcp\pyproject.toml
```

If `localhost:1010` refuses the connection, open GemLogin and wait for the UI/API to finish starting.

## Install Or Refresh

Install from the local repo so the MCP entrypoint is available:

```bash
python -m pip install -e /path/to/gemlogin-mcp
```

Smoke-run the server only through an MCP inspector/client because it speaks stdio:

```bash
python -m gemlogin_mcp.server
```

Stop it with `Ctrl+C` if started manually.

If you want a stable Codex registration, prefer a dedicated Python interpreter for this MCP install:

- Windows example: `C:\Users\pajipan\.codex\venvs\gemlogin-mcp\Scripts\python.exe`
- macOS example: `/Users/pajipan/.codex/venvs/gemlogin-mcp/bin/python`

## Register With MCP Clients

For Codex:

```bash
codex mcp add gemlogin -- /absolute/path/to/python -m gemlogin_mcp.server
codex mcp list
```

Use MCP env overrides when first-run profile startup is slow:

```bash
codex mcp add gemlogin \
  --env GEMLOGIN_TIMEOUT=120 \
  -- /absolute/path/to/python -m gemlogin_mcp.server
```

For Claude Code:

```bash
claude mcp add gemlogin -- /absolute/path/to/python -m gemlogin_mcp.server
claude mcp list
```

For Cursor, add this to the MCP config:

```json
{
  "mcpServers": {
    "gemlogin": {
      "command": "/absolute/path/to/python",
      "args": ["-m", "gemlogin_mcp.server"]
    }
  }
}
```

For clients that need environment overrides:

```json
{
  "mcpServers": {
    "gemlogin": {
      "command": "/absolute/path/to/python",
      "args": ["-m", "gemlogin_mcp.server"],
      "env": {
        "GEMLOGIN_BASE": "http://localhost:1010",
        "GEMLOGIN_TIMEOUT": "120"
      }
    }
  }
}
```

Cloud script execution also needs `GEMLOGIN_CLOUD_DEVICE_ID`, `GEMLOGIN_CLOUD_SOFT_ID`, and `GEMLOGIN_CLOUD_TOKEN`. Do not print or commit token values.

## Tool Map

Once the MCP server is connected, use these tools:

- `gemlogin_status`: check GemLogin local API status.
- `gemlogin_list_profiles`: list browser profiles.
- `gemlogin_get_profile(profile_id)`: inspect one profile.
- `gemlogin_start_profile(profile_id)`: start a profile and return `remote_debugging_address`, `browser_location`, and `driver_path`.
- `gemlogin_stop_profile(profile_id)`: close a profile.
- `gemlogin_list_groups`: list profile groups.
- `gemlogin_list_scripts`: list local automation scripts with sensitive defaults masked by default.
- `gemlogin_find_script(script_name)`: find a local script by name.
- `gemlogin_execute_local_script`: run a local script for one or more profiles.
- `gemlogin_check_local_script_status`: check one script/profile run.
- `gemlogin_kill_local_script`: stop one script/profile run.
- `gemlogin_cloud_execscript`: trigger a cloud workflow through GemLogin SaaS.

Resources:

- `gemlogin://status`
- `gemlogin://profiles`
- `gemlogin://profile/{id}`

Prompts:

- `warm_profile(profile_id, minutes)`
- `post_to_group(group_name, content)`

## Operating Rules

- Never expose `GEMLOGIN_CLOUD_TOKEN`, cookies, session values, or profile secrets in chat, commits, logs, or screenshots.
- Prefer `gemlogin_start_profile` followed by attaching Playwright/Puppeteer/Selenium to the returned `remote_debugging_address`.
- Always close profiles with `gemlogin_stop_profile` when the task is finished unless the user asks to keep them open.
- For script execution by name, prefer exact script names. Use `gemlogin_find_script` before fuzzy matching.
- Increase `GEMLOGIN_TIMEOUT` to `120` for first-run Chromium downloads or slow profile starts.
- If the MCP client cannot see tools after registration, restart that client.

## Troubleshooting

- `connection refused :1010`: GemLogin app is not running or the local API is not ready.
- MCP command not found or import failure: run `python -m pip install -e /path/to/gemlogin-mcp`, then reopen the terminal/client.
- Start profile times out: set `GEMLOGIN_TIMEOUT=120` in the MCP server env.
- Wrong API host: set `GEMLOGIN_BASE` in the MCP client config before launching the client.
- Cloud webhook failure: verify `device_id`, `soft_id`, `token`, and `workflow_id`; auth is sent as the `token` body field, not a Bearer header.

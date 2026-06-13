---
name: facebook-ads
description: Run and use local Facebook Ads MCP server from D:\Project\mcp-facebook-ads. Use when the user asks to start, stop, check, or call Facebook Ads MCP tools such as list_ad_accounts, list_campaigns, create_campaign, pause_campaign, list_ads, list_adsets, create_ad, pause_ad, get_account_insights, get_campaign_insights, get_campaign_performance, or get_top_performing_ads.
---

# Facebook Ads

Use this skill to operate the local Facebook Ads MCP server at `D:\Project\mcp-facebook-ads`.

When this skill is invoked:

1. Ensure credentials exist in `FB_ACCESS_TOKEN` or `META_ACCESS_TOKEN`.
2. Ensure PM2 app `facebook-ads` is running. If not, start it from local repo.
3. Use helper script for MCP JSON-RPC calls instead of hand-writing stdin protocol each time.

## Quick Checks

```powershell
python C:\Users\pajipan\.codex\skills\facebook-ads\scripts\facebook_ads_mcp.py status
python C:\Users\pajipan\.codex\skills\facebook-ads\scripts\facebook_ads_mcp.py ensure-running
python C:\Users\pajipan\.codex\skills\facebook-ads\scripts\facebook_ads_mcp.py tools-list
```

## Tool Calls

List tools:

```powershell
python C:\Users\pajipan\.codex\skills\facebook-ads\scripts\facebook_ads_mcp.py tools-list
```

Call one tool:

```powershell
python C:\Users\pajipan\.codex\skills\facebook-ads\scripts\facebook_ads_mcp.py call --tool list_campaigns --arguments "{\"ad_account_id\":\"1234567890\",\"limit\":10}"
```

PowerShell-safe JSON:

```powershell
$args = @{
  ad_account_id = "1234567890"
  limit = 10
} | ConvertTo-Json -Compress

$args | python C:\Users\pajipan\.codex\skills\facebook-ads\scripts\facebook_ads_mcp.py call --tool list_campaigns --arguments-stdin
```

Examples:

```powershell
python C:\Users\pajipan\.codex\skills\facebook-ads\scripts\facebook_ads_mcp.py call --tool list_ad_accounts
python C:\Users\pajipan\.codex\skills\facebook-ads\scripts\facebook_ads_mcp.py call --tool get_account_insights --arguments "{\"date_preset\":\"last_30d\"}"
python C:\Users\pajipan\.codex\skills\facebook-ads\scripts\facebook_ads_mcp.py call --tool get_top_performing_ads --arguments "{\"sort_by\":\"ctr\",\"limit\":5}"
```

## Tool Map

- `list_ad_accounts`
- `list_campaigns`
- `create_campaign`
- `pause_campaign`
- `get_campaign_insights`
- `list_ads`
- `list_adsets`
- `create_ad`
- `pause_ad`
- `get_account_insights`
- `get_campaign_performance`
- `get_top_performing_ads`

## Operating Rules

- Never print or commit `FB_ACCESS_TOKEN` or `META_ACCESS_TOKEN`.
- Prefer `python ...facebook_ads_mcp.py call --tool ...` for actual work. It auto-checks runtime and credentials first.
- If PM2 app is offline, `ensure-running`, `tools-list`, and `call` will start it automatically.
- For one-off debugging, direct `python D:\Project\mcp-facebook-ads\server.py` is still valid, but helper script is preferred.

## Troubleshooting

- `Missing FB_ACCESS_TOKEN or META_ACCESS_TOKEN`: set token in environment or Windows user environment.
- `pm2 not found`: install PM2 globally with npm or run `python D:\Project\mcp-facebook-ads\server.py` manually.
- `Tool call failed`: inspect `D:\Project\mcp-facebook-ads\logs\error.log` and rerun with `FB_MCP_DEBUG=1`.
- `Meta API request failed`: token, permissions, or ad account access likely wrong.

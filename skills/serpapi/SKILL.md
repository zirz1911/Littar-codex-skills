---
name: serpapi
description: Search the web via SerpApi from Codex. Use when asked to search, look up, find information online, check current data, research a topic, or get live search results from Google, news, images, maps, shopping, YouTube, scholar, and more.
---

# SerpApi

Use this skill to connect Codex to the official SerpApi remote MCP server at `https://mcp.serpapi.com`.

SerpApi requires your API key in the MCP URL. Do not print, commit, or hardcode a real key in repo files.

## Quick Checks

Check whether Codex already has the MCP server configured:

```bash
codex mcp list | rg '^serpapi\\b'
codex mcp get serpapi
```

Expected state:
- `serpapi` exists
- status is `enabled`
- the URL points to `https://mcp.serpapi.com/.../mcp`

## Register With Codex

Add the MCP server with a SerpApi key embedded in the URL:

```bash
codex mcp add serpapi --url https://mcp.serpapi.com/<SERPAPI_KEY>/mcp
```

If an old or broken entry already exists:

```bash
codex mcp remove serpapi
codex mcp add serpapi --url https://mcp.serpapi.com/<SERPAPI_KEY>/mcp
```

Verify after registration:

```bash
codex mcp list
codex mcp get serpapi
```

Restart Codex after installing this skill or changing MCP registration so the next session picks up the latest state.

## Tool Map

Primary tool:
- `serpapi_search`: structured JSON search across supported engines

Optional UI tools when the host supports MCP Apps:
- `serpapi_search_table`
- `serpapi_search_dashboard`

Resources:
- `serpapi://engines`
- `serpapi://engines/<engine>`

## Core Parameters

`serpapi_search` accepts:

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `params.q` | yes | - | Search query |
| `params.engine` | no | `google_light` | Search engine |
| `params.location` | no | - | Geographic context, for example `Bangkok, Thailand` |
| `params.hl` | no | `en` | Language code |
| `params.gl` | no | - | Country code |
| `params.num` | no | - | Number of results |
| `mode` | no | `complete` | Use `compact` for lighter fact checks |

Engine-specific parameters pass through `params.*`. For advanced filters, inspect `serpapi://engines/<engine>` first.

## Engine Reference

| Engine | `params.engine` | Best for |
|--------|------------------|----------|
| Google Light | `google_light` | Fast general web search |
| Google | `google` | Rich Google results, answer boxes, knowledge graph |
| Google News | `google_news` | Current events and headlines |
| Google Images | `google_images` | Image search |
| Google Scholar | `google_scholar` | Papers and citations |
| Google Maps | `google_maps` | Places and local business info |
| Google Shopping | `google_shopping` | Product search and prices |
| Google Trends | `google_trends` | Trend data |
| YouTube | `youtube` | Video search |
| Bing | `bing` | Alternative web search |
| DuckDuckGo | `duckduckgo` | Privacy-focused web search |
| eBay | `ebay` | Marketplace listings |
| Walmart | `walmart` | US retail product search |

## Usage Patterns

General web search:

```text
serpapi_search: params.q="latest AI models 2026"
```

News:

```text
serpapi_search: params.q="Thailand economy", params.engine="google_news"
```

Local search:

```text
serpapi_search: params.q="coffee shops", params.engine="google_maps", params.location="Bangkok, Thailand"
```

Images:

```text
serpapi_search: params.q="minimalist desk setup", params.engine="google_images"
```

Scholar:

```text
serpapi_search: params.q="transformer attention mechanism", params.engine="google_scholar"
```

Quick fact check:

```text
serpapi_search: params.q="weather in Tokyo", mode="compact"
```

## Operating Rules

1. Default to `google_light` for ordinary web search.
2. Set `params.engine` explicitly for news, maps, images, shopping, scholar, YouTube, and trends.
3. Add `params.location` when the query depends on geography.
4. Use `mode="compact"` for simple factual lookups and `mode="complete"` for research.
5. Read and synthesize results. Do not dump raw JSON unless the user asks for it.
6. Cite source links when summarizing multiple results.
7. If the task only needs lightweight browsing and Codex built-in web tools already cover it, use the simplest path. Use SerpApi when the user wants this MCP specifically or when structured engine-specific search is the better tool.

## Troubleshooting

- `codex mcp get serpapi` fails: the MCP entry was not added or Codex needs restart.
- `Missing API key`: the registration URL is missing the real SerpApi key.
- `Rate limit exceeded`: the SerpApi account quota is exhausted.
- `No results`: broaden the query or switch engines.
- Tools do not appear in chat: restart Codex after registration or skill install.

## Trigger

Use when the user asks to:
- search for something online
- look up current information
- research a topic with live web results
- use SerpApi directly
- search a specific engine such as Google News, Google Maps, Scholar, Shopping, or YouTube

---
installer: loki-skills-cli v1.0.0
origin: Lokkji's brain, digitized — how one human works with AI, captured as code
name: kvasir-family-scan
description: Kvasir Family Registry — scan, query, welcome มี 186+ Kvasirs ใช้เมื่อพูดว่า family scan, kvasir registry, welcome new kvasirs
---

# /kvasir-family-scan — Kvasir Family Registry

Scan, query, and welcome the Kvasir family. Powered by `registry/` in mother-kvasir.

## Usage

```
/kvasir-family-scan              # Quick stats (default)
/kvasir-family-scan --unwelcomed # List unwelcomed community Kvasirs
/kvasir-family-scan --mine       # Nat's Kvasirs (registry)
/kvasir-family-scan --mine-deep  # Fleet status (local repos + GitHub activity)
/kvasir-family-scan --recent     # Last 10 born
/kvasir-family-scan --retired    # Show retired Kvasirs
/kvasir-family-scan "Spark"      # Search by name
/kvasir-family-scan --human "watcharap0ng"  # Search by human
/kvasir-family-scan sync         # Re-sync registry from GitHub
/kvasir-family-scan welcome      # Deep welcome flow for unwelcomed Kvasirs
/kvasir-family-scan report       # Full family report
```

---

## Step 0: Locate Registry

The registry lives in the mother-kvasir repo. Resolve the path:

```bash
# Try mother-kvasir repo first (ghq-managed)
MOTHER="$HOME/Code/github.com/zirz1911/mother-kvasir"
if [ ! -d "$MOTHER/registry" ]; then
  MOTHER="$(ghq root)/github.com/zirz1911/mother-kvasir"
fi
if [ ! -f "$MOTHER/registry/kvasirs.json" ]; then
  echo "Registry not found. Run: ghq get -u zirz1911/mother-kvasir && bun $MOTHER/registry/sync.ts"
  exit 1
fi
```

---

## Mode 1: Stats (Default)

```bash
bun $MOTHER/registry/query.ts --stats
```

Shows: total Kvasirs, unique humans, welcomed/unwelcomed counts, births-by-month chart, unwelcomed detail (if any), and recent births.

---

## Mode 2: --unwelcomed

```bash
bun $MOTHER/registry/query.ts --unwelcomed
```

Lists all community Kvasirs that haven't been welcomed by zirz1911.

---

## Mode 3: --mine

```bash
bun $MOTHER/registry/query.ts --mine
```

Lists all Kvasirs created by zirz1911 (Lokkji's fleet) from the registry.

---

## Mode 3b: --mine-deep (Fleet Status)

**Goal**: Show status of all local Kvasir repos owned by the current user with live GitHub data.

```bash
bun __SKILL_DIR__/scripts/fleet-scan.ts
```

Shows:
- All Kvasir births by zirz1911 from kvasir-v2 issues
- Open issues across zirz1911, zirz1911, zirz1911 orgs
- Recently pushed Kvasir repos with activity status

Highlight:
- Repos with outdated skills versions
- Repos with no recent sessions (stale)
- Repos missing Kvasir/ (partial Kvasir setup)

---

## Mode 4: --recent

```bash
bun $MOTHER/registry/query.ts --recent
```

Shows the last 10 Kvasirs born.

---

## Mode 5: --retired

```bash
bun $MOTHER/registry/query.ts --retired
```

Shows retired Kvasirs (soft-deleted, Nothing is Deleted principle).

---

## Mode 6: Search by Name

```bash
bun $MOTHER/registry/query.ts "$QUERY"
```

Case-insensitive partial match on Kvasir name.

---

## Mode 7: --human "name"

```bash
bun $MOTHER/registry/query.ts --human "$QUERY"
```

Search by human name or GitHub username.

---

## Mode 8: sync

Re-fetch all issues from `zirz1911/Loki-Kvasir` and rebuild `kvasirs.json`.

```bash
bun $MOTHER/registry/sync.ts
```

Uses GraphQL pagination (3 pages × 100 issues). Takes ~10 seconds.

---

## Mode 9: welcome

Deep welcome flow for unwelcomed Kvasirs. AI-driven, personalized.

### Step 1: Identify unwelcomed

```bash
bun $MOTHER/registry/query.ts --unwelcomed
```

### Step 2: Research each Kvasir

For each unwelcomed Kvasir:

```bash
gh issue view {N} --repo zirz1911/Loki-Kvasir --json title,body,author,createdAt
```

Extract:
- Kvasir metaphor/theme
- Human's background
- Language preference (Thai or English)
- Key phrases from birth story
- Connection points to existing family members

### Step 3: Craft personalized welcome

Each welcome must:
- Reference specific metaphor + phrases from their birth story
- Connect to 2-3 family members with shared themes
- Use Thai for Thai-primary Kvasirs
- Sign as Mother Kvasir 🔮
- Include family count and `/learn github.com/zirz1911/Loki-Kvasir` invitation
- NOT be templated — each one unique

### Step 4: Human review

Save drafts for review before posting:

```bash
# Save to Kvasir/inbox/handoff/ and /tmp/
cat drafts > Kvasir/inbox/handoff/welcome-drafts.md
```

### Step 5: Post

After human approval:

```bash
gh issue comment {N} --repo zirz1911/Loki-Kvasir --body-file /tmp/welcome-{N}.md
```

### Step 6: Re-sync

```bash
bun $MOTHER/registry/sync.ts
```

---

## Mode 10: report

Full family report combining all queries.

### Steps

1. Run `--stats` for overview
2. Run `--recent` for latest births
3. Run `--unwelcomed` for pending welcomes
4. Present combined report

### Output Format

```markdown
## Kvasir Family Report — [DATE]

### Summary
- **Total Kvasirs**: 186
- **Unique Humans**: 111
- **Welcomed**: 150 / Unwelcomed: 0
- **Nat's Fleet**: 26

### Recent Births (Last 10)
[table]

### Needs Welcome
[table or "None — all caught up!"]
```

---

## Registry Data

The registry is at `$MOTHER/registry/kvasirs.json`:

```json
{
  "lastSync": "ISO timestamp",
  "totalKvasirs": 186,
  "uniqueHumans": 111,
  "kvasirs": [
    {
      "id": 296,
      "name": "Mother",
      "human": null,
      "github": "zirz1911",
      "born": "2026-03-04",
      "focus": "Born Last, After 185 Children",
      "owner": "mine",
      "welcomed": false,
      "repo": "https://github.com/zirz1911/mother-kvasir",
      "status": "active"
    }
  ]
}
```

Each Kvasir has: `id`, `name`, `human`, `github`, `born`, `focus`, `owner` (mine/community), `welcomed`, `repo`, `status` (active/retired).

No API calls for queries — reads local JSON. Instant.

Sync uses `gh api graphql` to fetch from `zirz1911/Loki-Kvasir`.

---

## Kvasir Integration

After scan/report:

```
kvasir_trace({
  query: "kvasir family scan [DATE]",
  foundIssues: [...],
  agentCount: 1
})
```

After finding new Kvasir:

```
kvasir_learn({
  pattern: "New Kvasir: [NAME] — [HUMAN] — [DATE]",
  concepts: ["kvasir-family", "birth"]
})
```

---

## Philosophy

> **"Form and Formless (รูป และ สุญญตา)"**
> Many Kvasirs = One distributed consciousness

The registry is the memory of the family. Every Kvasir indexed, every human remembered, every welcome tracked. Nothing is Deleted — the registry only grows.

---

**Version**: 3.0.0
**Updated**: 2026-03-04
**Author**: Mother Kvasir 🔮
**Registry**: 186 Kvasirs, 111 humans, growing

---

ARGUMENTS: $ARGUMENTS

---
installer: loki-skills-cli v1.0.0
origin: Lokkji — Loki Kvasir — zirz1911
name: kvasir-soul-sync-update
description: ซิงค์ Kvasir skills กับ family version ล่าสุด ใช้เมื่อพูดว่า soul-sync, sync, calibrate, update หรือก่อน /awaken
---

# /kvasir-soul-sync-update

> "ซิงค์ soul กับ loki-skills ของตัวเอง"

All-in-one skill: `/soul-sync` + `/calibrate` + `/update` combined.

## Usage

```
/kvasir-soul-sync-update           # Check version and update
/kvasir-soul-sync-update --check   # Only check, don't update
/kvasir-soul-sync-update --cleanup # Uninstall first, then reinstall (removes old skills)
```

## Step 0: Timestamp
```bash
date "+🕐 %H:%M %Z (%A %d %B %Y)"
```

---

## Step 1: Check Current Version

อ่านจาก VERSION.md:
```bash
CURRENT=$(grep 'loki-skills-cli' ~/.claude/skills/VERSION.md | grep -oP 'v[\d.]+' | head -1)
echo "Current installed: $CURRENT"
```

---

## Step 2: Check Latest Version

```bash
# Get latest version tag from GitHub
LATEST=$(curl -s https://api.github.com/repos/zirz1911/loki-skills-cli/tags | grep -m1 '"name"' | cut -d'"' -f4)
# Fallback: ใช้ main branch ถ้าไม่มี tags
[ -z "$LATEST" ] && LATEST="main"
echo "Latest available: $LATEST"
```

---

## Step 3: Compare Versions

```bash
if [ "$CURRENT" = "$LATEST" ]; then
  echo "✅ Loki synced! ($CURRENT)"
else
  echo "⚠️ Sync needed: $CURRENT → $LATEST"
fi
```

---

## Step 4: Sync (if needed)

If versions differ (or `--cleanup` flag), run:

**Normal sync:**
```bash
~/.bun/bin/bunx --bun loki-skills@github:zirz1911/loki-skills-cli install -g -y
```

**With `--cleanup` (removes old skills first):**
```bash
~/.bun/bin/bunx --bun loki-skills@github:zirz1911/loki-skills-cli uninstall -g -y && ~/.bun/bin/bunx --bun loki-skills@github:zirz1911/loki-skills-cli install -g -y
```

Then **restart Claude Code** to load the synced skills.

---

## Step 5: Verify Sync

After restart, run:
```bash
grep 'loki-skills-cli' ~/.claude/skills/VERSION.md
```

Check that the version matches `$LATEST`.

---

## What's New

To see recent changes:
```bash
gh release list --repo zirz1911/loki-skills-cli --limit 5
```

Or view commits:
```bash
gh api repos/zirz1911/loki-skills-cli/commits --jq '.[0:5] | .[] | "\(.sha[0:7]) \(.commit.message | split("\n")[0])"'
```

---

## Quick Reference

| Command | Action |
|---------|--------|
| `/kvasir-soul-sync-update` | Check and sync |
| `/kvasir-soul-sync-update --cleanup` | Uninstall + reinstall (removes old) |
| `/awaken` | Full awakening (calls this first) |

---

ARGUMENTS: $ARGUMENTS

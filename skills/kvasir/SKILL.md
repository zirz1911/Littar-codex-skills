---
installer: loki-skills-cli v1.0.0
origin: Lokkji's brain, digitized — how one human works with AI, captured as code
name: kvasir
description: จัดการ Kvasir skills และ profiles ใช้เมื่อพูดว่า kvasir, profile, install skill, remove skill
---

# /kvasir

> Skill and profile management for Kvasir instruments.

## Usage

```
/kvasir prepare              # check & install git, gh, ghq; set up gh auth
/kvasir profile              # list available profiles
/kvasir profile <name>       # switch to a profile
/kvasir install <skill>      # install one skill
/kvasir remove <skill>       # remove one skill
/kvasir skills               # list installed skills
```

---

## Subcommands

### /kvasir prepare

Check for required tools and install any that are missing. Set up `gh` auth if needed.

**First, detect the platform** by checking the runtime environment (e.g. `uname` or `$OSTYPE`):

| Platform | Package manager |
|----------|----------------|
| macOS | `brew install <pkg>` |
| Linux (Debian/Ubuntu) | `sudo apt install <pkg>` (use official gh repo for gh) |
| Linux (Fedora/RHEL) | `sudo dnf install <pkg>` |
| Linux (Arch) | `sudo pacman -S <pkg>` |
| Windows | `winget install <pkg>` or `scoop install <pkg>` |

**Steps (run each in order):**

1. **Check git**: `git --version`
   - If missing, install with the platform's package manager
2. **Check gh**: `gh --version`
   - If missing, install:
     - macOS: `brew install gh`
     - Debian/Ubuntu: follow https://github.com/cli/cli/blob/trunk/docs/install_linux.md
     - Windows: `winget install GitHub.cli`
     - Others: platform package manager
3. **Check gh auth**: `gh auth status`
   - If not authenticated: run `gh auth login` and guide the user through it
4. **Check ghq**: `ghq --version`
   - If missing, install:
     - macOS: `brew install ghq`
     - Linux/Windows: `go install github.com/x-motemen/ghq@latest` (needs Go), or download binary from GitHub releases
5. **Check ghq root**: `ghq root`
   - If not set, suggest: `git config --global ghq.root ~/Code`

Print a summary table at the end:

```
Platform: macOS / Linux (Ubuntu) / Windows
Tool    Status
----    ------
git     ✓ installed (2.x.x)
gh      ✓ installed + authenticated
ghq     ✓ installed (root: ~/Code)
```

If everything is already set up, just print the summary — no changes needed.

### /kvasir profile

List available profiles.

```bash
kvasir-skills profiles
```

### /kvasir profile \<name\>

Switch to a profile (installs that profile's skill set).

Profiles: `seed`/`minimal` (6 skills), `standard` (12 skills), `full` (all)

```bash
kvasir-skills install -g -y --profile <name>
```

### /kvasir install \<skill\>

Install a single skill.

```bash
kvasir-skills install -g -y --skill <skill>
```

### /kvasir remove \<skill\>

Uninstall a single skill.

```bash
kvasir-skills uninstall -g -y --skill <skill>
```

### /kvasir skills

List installed skills.

```bash
kvasir-skills list -g
```

---

## Quick Reference

| Command | Action |
|---------|--------|
| `/kvasir prepare` | Check & install git, gh, ghq; set up gh auth |
| `/kvasir profile` | List available profiles |
| `/kvasir profile seed` | Switch to seed profile |
| `/kvasir install <skill>` | Install one skill |
| `/kvasir remove <skill>` | Remove one skill |
| `/kvasir skills` | List installed skills |

---

ARGUMENTS: $ARGUMENTS

# Littar Codex Skills

Portable installer for the local Codex skills used by Littar-Codex.

## Install

```bash
git clone git@github.com:zirz1911/Littar-codex-skills.git
cd Littar-codex-skills
./install.sh /path/to/target-repo
```

Install only selected skills:

```bash
./install.sh /path/to/target-repo --only genz-cut cut-silence
```

List bundled skills:

```bash
./install.sh --list
```

The installer copies skills into `.agents/skills/`, `.claude/skills/`, and `~/.codex/skills/`, then updates `skills-lock.json`.

#!/usr/bin/env python3
"""Install bundled Codex skills into a target repository.

Copies ./skills/* to the repo-local agent folders and the user's Codex
skills directory, then updates <target>/skills-lock.json with local
entries and SHA-256 hashes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent
SOURCE_SKILLS = REPO_ROOT / "skills"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict:
    if not path.exists():
        return {"version": 1, "skills": {}}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def install_skill_dir(source: Path, destination_root: Path) -> None:
    destination_root.mkdir(parents=True, exist_ok=True)
    dest = destination_root / source.name
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(source, dest)


def main() -> int:
    parser = argparse.ArgumentParser(description="Install Littar Codex skills into a repository")
    parser.add_argument("target", nargs="?", default=".", help="Target repository path, default: current directory")
    parser.add_argument("--only", nargs="*", help="Install only these skill names")
    parser.add_argument("--list", action="store_true", help="List bundled skills and exit")
    args = parser.parse_args()

    skill_dirs = sorted(path for path in SOURCE_SKILLS.iterdir() if (path / "SKILL.md").is_file())
    if args.list:
        for skill_dir in skill_dirs:
            print(skill_dir.name)
        return 0

    selected = set(args.only or [])
    if selected:
        missing = selected - {path.name for path in skill_dirs}
        if missing:
            raise SystemExit(f"Unknown bundled skill(s): {', '.join(sorted(missing))}")
        skill_dirs = [path for path in skill_dirs if path.name in selected]

    target = Path(args.target).expanduser().resolve()
    install_roots = [
        target / ".agents" / "skills",
        target / ".claude" / "skills",
        Path.home() / ".codex" / "skills",
    ]

    lock_path = target / "skills-lock.json"
    lock = load_json(lock_path)
    lock.setdefault("version", 1)
    lock.setdefault("skills", {})

    installed = []
    for skill_dir in skill_dirs:
        for install_root in install_roots:
            install_skill_dir(skill_dir, install_root)

        skill_md = skill_dir / "SKILL.md"
        lock["skills"][skill_dir.name] = {
            "source": "Littar-codex-skills",
            "sourceType": "local",
            "skillPath": f"skills/{skill_dir.name}/SKILL.md",
            "computedHash": sha256_file(skill_md),
        }
        installed.append(skill_dir.name)

    with lock_path.open("w", encoding="utf-8") as handle:
        json.dump(lock, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    print(f"Installed {len(installed)} skill(s) into {target}")
    print(f"Synced local Codex skills into {Path.home() / '.codex' / 'skills'}")
    for name in installed:
        print(f"- {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

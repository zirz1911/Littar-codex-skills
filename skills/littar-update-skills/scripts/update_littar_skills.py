#!/usr/bin/env python3
"""Update and install Littar Codex skills from the source repository."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


DEFAULT_REPO_URL = "https://github.com/zirz1911/Littar-codex-skills.git"


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    print("+ " + " ".join(cmd), flush=True)
    return subprocess.run(cmd, cwd=cwd, text=True, check=True)


def capture(cmd: list[str], cwd: Path | None = None) -> str:
    return subprocess.check_output(cmd, cwd=cwd, text=True).strip()


def ensure_repo(repo: Path, repo_url: str) -> None:
    if repo.exists():
        if not (repo / ".git").is_dir():
            raise SystemExit(f"Source path exists but is not a git repo: {repo}")
        return

    repo.parent.mkdir(parents=True, exist_ok=True)
    run(["git", "clone", repo_url, str(repo)])


def update_repo(repo: Path, skip_pull: bool) -> None:
    if skip_pull:
        print(f"Skipping git pull for {repo}", flush=True)
        return

    status = capture(["git", "status", "--short"], cwd=repo)
    if status:
        raise SystemExit(
            "Source repo has uncommitted changes; refusing to pull.\n"
            f"Repo: {repo}\n"
            f"{status}\n"
            "Commit/stash those changes, or rerun with --skip-pull to install the current checkout."
        )

    run(["git", "pull", "--ff-only"], cwd=repo)


def install_skills(repo: Path, target: Path, only: list[str] | None) -> None:
    install_py = repo / "install.py"
    if not install_py.is_file():
        raise SystemExit(f"Missing installer: {install_py}")

    cmd = [sys.executable, str(install_py), str(target)]
    if only:
        cmd.extend(["--only", *only])
    run(cmd)


def main() -> int:
    parser = argparse.ArgumentParser(description="Update and install Littar Codex skills")
    parser.add_argument(
        "--repo",
        default=os.environ.get("LITTAR_CODEX_SKILLS_REPO", "~/Project/Littar-codex-skills"),
        help="Local Littar-codex-skills checkout",
    )
    parser.add_argument(
        "--repo-url",
        default=os.environ.get("LITTAR_CODEX_SKILLS_REPO_URL", DEFAULT_REPO_URL),
        help="Git URL used when the local checkout is missing",
    )
    parser.add_argument(
        "--target",
        default=os.environ.get("LITTAR_CODEX_TARGET", "."),
        help="Target Codex workspace to receive .agents/skills",
    )
    parser.add_argument("--skip-pull", action="store_true", help="Install current checkout without git pull")
    parser.add_argument("--only", nargs="*", help="Install only selected skills")
    args = parser.parse_args()

    repo = Path(args.repo).expanduser().resolve()
    target = Path(args.target).expanduser().resolve()

    ensure_repo(repo, args.repo_url)
    update_repo(repo, args.skip_pull)
    install_skills(repo, target, args.only)

    print(f"Done. Installed Littar Codex skills from {repo} into {target}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path

DEFAULT_ROOT = Path(r"C:/Users/pajipan/AppData/Local/CapCut/User Data/Projects/com.lveditor.draft")


def _iter_projects(root: Path):
    for entry in sorted(root.iterdir()):
        if entry.is_dir() and (entry / "draft_meta_info.json").is_file():
            yield entry


def find_project(root: Path, name: str) -> list[Path]:
    hits: list[Path] = []
    needle = name.casefold()
    for project in _iter_projects(root):
        meta = json.loads((project / "draft_meta_info.json").read_text(encoding="utf-8"))
        draft_name = str(meta.get("draft_name", ""))
        if needle in draft_name.casefold() or needle in project.name.casefold():
            hits.append(project)
    return hits


def backup_project(project: Path) -> Path:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = project / "_backup" / ts
    backup_dir.mkdir(parents=True, exist_ok=True)
    for name in ["draft_content.json", "template-2.tmp", "draft_meta_info.json"]:
        src = project / name
        if src.exists():
            shutil.copy2(src, backup_dir / name)
    timelines = project / "Timelines"
    if timelines.exists():
        for tl in timelines.iterdir():
            if not tl.is_dir():
                continue
            tl_backup = backup_dir / "Timelines" / tl.name
            tl_backup.mkdir(parents=True, exist_ok=True)
            for name in ["draft_content.json", "template-2.tmp", "draft_meta_info.json"]:
                src = tl / name
                if src.exists():
                    shutil.copy2(src, tl_backup / name)
    return backup_dir


def sync_file_to_timelines(project: Path, filename: str) -> int:
    src = project / filename
    if not src.is_file():
        raise FileNotFoundError(f"Missing source file: {src}")
    timelines = project / "Timelines"
    if not timelines.exists():
        return 0
    count = 0
    for tl in timelines.iterdir():
        if not tl.is_dir():
            continue
        dest = tl / filename
        if dest.exists():
            shutil.copy2(src, dest)
            count += 1
    return count


def validate_json_files(project: Path) -> list[Path]:
    checked: list[Path] = []
    for rel in ["draft_content.json", "template-2.tmp", "draft_meta_info.json"]:
        p = project / rel
        if p.exists():
            json.loads(p.read_text(encoding="utf-8"))
            checked.append(p)
    timelines = project / "Timelines"
    if timelines.exists():
        for tl in timelines.iterdir():
            if not tl.is_dir():
                continue
            for rel in ["draft_content.json", "template-2.tmp", "draft_meta_info.json"]:
                p = tl / rel
                if p.exists():
                    json.loads(p.read_text(encoding="utf-8"))
                    checked.append(p)
    return checked


def main() -> int:
    parser = argparse.ArgumentParser(description="CapCut draft helper")
    parser.add_argument("--root", default=str(DEFAULT_ROOT), help="CapCut draft root directory")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_find = sub.add_parser("find", help="Find project by name")
    p_find.add_argument("--name", required=True)

    p_backup = sub.add_parser("backup", help="Backup project JSON files")
    p_backup.add_argument("--project", required=True)

    p_sync = sub.add_parser("sync", help="Copy root file to each timeline copy")
    p_sync.add_argument("--project", required=True)
    p_sync.add_argument("--file", required=True, choices=["draft_content.json", "template-2.tmp", "draft_meta_info.json"])

    p_validate = sub.add_parser("validate", help="Validate JSON parse")
    p_validate.add_argument("--project", required=True)

    args = parser.parse_args()
    root = Path(args.root)

    if args.cmd == "find":
        hits = find_project(root, args.name)
        for p in hits:
            print(p)
        return 0 if hits else 1

    project = Path(args.project)
    if args.cmd == "backup":
        out = backup_project(project)
        print(out)
        return 0

    if args.cmd == "sync":
        count = sync_file_to_timelines(project, args.file)
        print(count)
        return 0

    if args.cmd == "validate":
        checked = validate_json_files(project)
        for p in checked:
            print(p)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())

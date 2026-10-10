"""Read-only inventory for the Paji-Cut queue and CapCut Template 1."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys

VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm"}
AUDIO_EXTS = {".mp3", ".m4a", ".aac", ".wav", ".flac", ".ogg"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}


def sort_key(path: Path) -> tuple[int, str]:
    name = path.name
    match = re.match(r"^\s*(\d+)(?=\D|$)", name)
    return (int(match.group(1)) if match else sys.maxsize, name.casefold())


def files_with_extensions(folder: Path, extensions: set[str]) -> list[Path]:
    return sorted(
        (path for path in folder.iterdir() if path.is_file() and path.suffix.lower() in extensions),
        key=lambda path: path.name.casefold(),
    )


def find_template(root: Path) -> tuple[Path, dict, dict]:
    matches = []
    for meta_path in root.glob("*/draft_meta_info.json"):
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if meta.get("draft_name") == "Template 1":
            matches.append((meta_path.parent, meta))
    if len(matches) != 1:
        raise ValueError(f"Expected one Template 1 under {root}; found {len(matches)}")
    project, meta = matches[0]
    content = json.loads((project / "draft_content.json").read_text(encoding="utf-8"))
    text_tracks = [track for track in content.get("tracks", []) if track.get("type") == "text"]
    if len(text_tracks) < 2 or any(not track.get("segments") for track in text_tracks[:2]):
        raise ValueError("Template 1 does not have the required two populated text tracks")
    return project, meta, content


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Single clip folder or parent of clip folders")
    parser.add_argument("--projects-root", type=Path, help="CapCut drafts directory; defaults to LOCALAPPDATA")
    args = parser.parse_args()
    folder = args.input.expanduser().resolve()
    if not folder.is_dir():
        parser.error(f"Input folder does not exist: {folder}")

    local_app_data = os.environ.get("LOCALAPPDATA")
    if args.projects_root:
        projects_root = args.projects_root.expanduser().resolve()
    elif local_app_data:
        projects_root = Path(local_app_data) / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft"
    else:
        parser.error("LOCALAPPDATA is missing; pass --projects-root")

    try:
        template, _, content = find_template(projects_root)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))

    direct_video = files_with_extensions(folder, VIDEO_EXTS)
    # `output` may contain a prior export/insert assets and is not another clip.
    children = sorted(
        (path for path in folder.iterdir() if path.is_dir() and path.name.casefold() != "output"),
        key=sort_key,
    )
    child_clips = [path for path in children if files_with_extensions(path, VIDEO_EXTS)]
    if direct_video and child_clips:
        parser.error("Video exists in both the parent and child folders; choose the clip root explicitly")
    if not direct_video:
        empty = [path.name for path in children if path not in child_clips]
        if empty:
            parser.error(f"Child folders without video: {', '.join(empty)}")
    clip_folders = [folder] if direct_video else child_clips
    if not clip_folders:
        parser.error("No video files found in the selected folder or its immediate child folders")

    print(f"Template: {template}")
    print(f"Template ID: {content.get('id')}")
    print(f"Queue: {len(clip_folders)} clip(s)")
    for index, clip in enumerate(clip_folders, 1):
        videos = files_with_extensions(clip, VIDEO_EXTS)
        audios = files_with_extensions(clip, AUDIO_EXTS)
        images = files_with_extensions(clip, IMAGE_EXTS)
        briefs = [name for name in ("brief.md", "brief.txt") if (clip / name).is_file()]
        print(f"\n{index}. {clip}")
        print(f"   video: {', '.join(path.name for path in videos)}")
        print(f"   audio candidates: {', '.join(path.name for path in audios) or '(none)'}")
        print(f"   existing images: {', '.join(path.name for path in images) or '(none)'}")
        print(f"   brief: {', '.join(briefs) or '(none)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

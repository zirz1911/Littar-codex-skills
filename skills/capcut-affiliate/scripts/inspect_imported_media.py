"""Read-only inventory of a CapCut draft's imported video and timeline state."""

import argparse
import json
import os
import sys
from pathlib import Path


VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm", ".mts"}


def projects_root():
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        raise ValueError("LOCALAPPDATA is not set")
    return Path(local_app_data) / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft"


def find_project(name, root):
    matches = []
    for folder in root.iterdir():
        metadata_file = folder / "draft_meta_info.json"
        if not folder.is_dir() or not metadata_file.is_file():
            continue
        try:
            metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if metadata.get("draft_name") == name:
            matches.append((folder, metadata))
    if len(matches) != 1:
        raise ValueError(f"Expected one draft named {name!r}; found {len(matches)}")
    return matches[0]


def resolve_media_path(project, raw_path):
    if not raw_path:
        return None
    if raw_path.startswith("./") or raw_path.startswith(".\\"):
        return project / raw_path[2:]
    return Path(raw_path)


def imported_videos(project, metadata):
    found = []
    seen = set()
    for group in metadata.get("draft_materials", []):
        for item in group.get("value", []):
            raw_path = item.get("file_Path", "")
            if Path(raw_path).suffix.lower() not in VIDEO_EXTENSIONS:
                continue
            path = resolve_media_path(project, raw_path)
            if raw_path in seen:
                continue
            seen.add(raw_path)
            found.append({
                "name": item.get("extra_info") or path.name,
                "path": str(path),
                "exists": path.is_file(),
                "duration_seconds": round(item.get("duration", 0) / 1_000_000, 3),
            })
    return found


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True, help="Exact CapCut draft_name")
    args = parser.parse_args()
    project, metadata = find_project(args.name, projects_root())
    content = json.loads((project / "draft_content.json").read_text(encoding="utf-8"))
    imported = imported_videos(project, metadata)
    embedded = [
        str(path)
        for path in (project / "video").rglob("*")
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS
    ] if (project / "video").is_dir() else []
    print(json.dumps({
        "draft_name": metadata.get("draft_name"),
        "project": str(project),
        "duration_seconds": round(content.get("duration", 0) / 1_000_000, 3),
        "main_track_video_segments": sum(
            len(track.get("segments", []))
            for track in content.get("tracks", []) if track.get("type") == "video"
        ),
        "timeline_video_materials": len(content.get("materials", {}).get("videos", [])),
        "imported_video_count": len(imported),
        "existing_imported_video_count": sum(item["exists"] for item in imported),
        "imported_videos": imported,
        "embedded_videos": embedded,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

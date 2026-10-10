"""Add or verify Ascen-style Type 1 typing-in on persistent CapCut text tracks."""

import argparse
import copy
import json
import sys
from pathlib import Path

import capcut_sfx as draft_io


TEMPLATE = Path(__file__).resolve().parent.parent / "references" / "typing-in-animation.json"
ANIMATION_NAME = "Type 1"
ANIMATION_DURATION = 500_000
ONE_FRAME = 33_334


def persistent_text_segments(draft):
    selected = []
    for track in draft["tracks"]:
        if track["type"] != "text" or len(track["segments"]) != 1:
            continue
        segment = track["segments"][0]
        span = segment["target_timerange"]
        if span["start"] == 0 and span["duration"] >= draft["duration"] - ONE_FRAME:
            selected.append(segment)
    return selected


def is_type_one(material):
    return (material.get("type") == "sticker_animation"
            and any(animation.get("name") == ANIMATION_NAME
                    and animation.get("type") == "in"
                    and animation.get("start") == 0
                    and animation.get("duration") == ANIMATION_DURATION
                    for animation in material.get("animations", [])))


def verify(draft):
    segments = persistent_text_segments(draft)
    index = draft_io.material_index(draft)
    failures = []
    if len(segments) != 2:
        failures.append(f"Expected two persistent text tracks; found {len(segments)}")
    details = []
    for position, segment in enumerate(segments, 1):
        refs = [index[ref][1] for ref in segment.get("extra_material_refs", []) if ref in index]
        matched = [material for material in refs if is_type_one(material)]
        paths = [Path(animation["path"]) for material in matched
                 for animation in material["animations"] if animation.get("name") == ANIMATION_NAME]
        valid = len(matched) == 1 and len(paths) == 1 and paths[0].exists()
        if not valid:
            failures.append(f"Text track {position} lacks a usable 0.5 s Type 1 entrance")
        details.append({"text_track": position, "typing_in": valid})
    return {"valid": not failures, "text_tracks": details, "failures": failures}


def add_typing(original):
    target = copy.deepcopy(original)
    template = draft_io.localize(draft_io.read_json(TEMPLATE)["material"])
    animation = template["animations"][0]
    if not is_type_one(template) or not Path(animation["path"]).exists():
        raise ValueError("CapCut Type 1 animation is not cached; apply Type 1 In in CapCut UI first")
    segments = persistent_text_segments(target)
    if len(segments) != 2:
        raise ValueError(f"Expected two persistent default-style text tracks; found {len(segments)}")
    index = draft_io.material_index(target)
    for segment in segments:
        current = [index[ref][1] for ref in segment.get("extra_material_refs", []) if ref in index]
        if any(material.get("type") == "sticker_animation" for material in current):
            raise ValueError("Text segment already has an animation; inspect before replacing it")
        material = copy.deepcopy(template)
        material["id"] = draft_io.fresh_id()
        target["materials"]["material_animations"].append(material)
        segment.setdefault("extra_material_refs", []).append(material["id"])
    checked = verify(target)
    if not checked["valid"]:
        raise ValueError(f"Typing-in verification failed: {checked['failures']}")
    if target["duration"] != original["duration"]:
        raise ValueError("Draft duration changed")
    for old_track, new_track in zip(original["tracks"], target["tracks"]):
        if old_track["type"] != "text" and old_track != new_track:
            raise ValueError("Non-text track changed")
    for kind, old_materials in original["materials"].items():
        if target["materials"][kind][:len(old_materials)] != old_materials:
            raise ValueError(f"Existing {kind} materials changed")
    return target


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["plan", "apply", "verify"])
    parser.add_argument("--name", required=True, help="Exact draft_meta_info.json draft_name")
    parser.add_argument("--project-dir", type=Path, help="Explicit draft directory for an offline fixture")
    args = parser.parse_args()
    project, metadata = draft_io.find_project(args.name, args.project_dir)
    original = draft_io.read_json(project / "draft_content.json")
    if args.action == "verify":
        result = verify(original)
    else:
        target = add_typing(original)
        result = {"valid": True, "draft": metadata["draft_name"],
                  "text_tracks": 2, "animation": ANIMATION_NAME,
                  "duration_seconds": ANIMATION_DURATION / 1_000_000,
                  "applied": args.action == "apply"}
        if args.action == "apply":
            result["backup"] = str(draft_io.apply(
                project, target, metadata, backup_prefix="before-typing-in"))
            checked = verify(draft_io.read_json(project / "draft_content.json"))
            if not checked["valid"]:
                raise ValueError(f"Post-write typing-in verification failed: {checked['failures']}")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

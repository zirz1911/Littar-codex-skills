"""Insert and verify saved CapCut Favorite sound effects in an editable draft.

Plan JSON example:
[{"sound":"keyboard","start_seconds":0,"volume":0.32},
 {"sound":"swish","start_seconds":1.6,"volume":0.28},
 {"sound":"pop","start_seconds":5.5,"volume":0.30}]
"""

import argparse
import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parent.parent
LIBRARY = SKILL_DIR / "references" / "capcut-favorite-sfx.json"
KEYBOARDS = {"keyboard", "keyboard_alternative"}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def project_root():
    return Path(os.environ["LOCALAPPDATA"]) / "CapCut" / "User Data" / "Projects" / "com.lveditor.draft"


def find_project(name, explicit_dir=None):
    if explicit_dir:
        folder = Path(explicit_dir).resolve()
        metadata = read_json(folder / "draft_meta_info.json")
        if metadata.get("draft_name") != name:
            raise ValueError("Project directory does not match the exact draft name")
        return folder, metadata
    matches = []
    for folder in project_root().iterdir():
        meta_path = folder / "draft_meta_info.json"
        if folder.is_dir() and meta_path.is_file():
            try:
                meta = read_json(meta_path)
            except (OSError, json.JSONDecodeError):
                continue
            if meta.get("draft_name") == name:
                matches.append((folder, meta))
    if len(matches) != 1:
        raise ValueError(f"Expected one draft named {name!r}, found {len(matches)}")
    return matches[0]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fresh_id():
    return str(uuid.uuid4()).upper()


def remap(value, ids):
    if isinstance(value, dict):
        return {key: remap(item, ids) for key, item in value.items()}
    if isinstance(value, list):
        return [remap(item, ids) for item in value]
    return ids.get(value, value) if isinstance(value, str) else value


def localize(value):
    if isinstance(value, dict):
        return {key: localize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [localize(item) for item in value]
    if isinstance(value, str):
        return value.replace("${LOCALAPPDATA}", os.environ["LOCALAPPDATA"].replace("\\", "/"))
    return value


def material_index(draft):
    index = {}
    for kind, materials in draft["materials"].items():
        if isinstance(materials, list):
            for material in materials:
                if isinstance(material, dict) and material.get("id"):
                    if material["id"] in index:
                        raise ValueError(f"Duplicate material ID: {material['id']}")
                    index[material["id"]] = (kind, material)
    return index


def parse_plan(path, library, duration):
    cues = read_json(path)
    if not isinstance(cues, list) or not 3 <= len(cues) <= 5:
        raise ValueError("Plan must contain 3–5 SFX cues")
    if cues[0].get("sound") not in KEYBOARDS or cues[0].get("start_seconds") != 0:
        raise ValueError("Default style requires a keyboard cue at 0 seconds")
    parsed = []
    for cue in cues:
        key = cue.get("sound")
        if key not in library["sounds"]:
            raise ValueError(f"Unknown CapCut Favorite sound key: {key}")
        try:
            start = round(float(cue["start_seconds"]) * 1_000_000)
            volume = float(cue["volume"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"Invalid cue timing/volume: {cue}") from error
        template = localize(library["sounds"][key])
        length = template["segment"]["target_timerange"]["duration"]
        path = Path(template["materials"]["audios"][0]["path"])
        if start < 0 or start + length > duration or not 0 < volume <= 1:
            raise ValueError(f"Cue outside draft or unsafe volume: {key}")
        if not path.is_file():
            raise ValueError(
                f"CapCut Favorite {key!r} is not cached at {path}. "
                "Add it from CapCut Sounds > Sound effects > Favorites first; no user audio upload is needed."
            )
        parsed.append({"key": key, "name": template["name"], "start": start,
                       "duration": length, "volume": volume, "template": template})
    return sorted(parsed, key=lambda item: item["start"])


def existing_saved_sfx(draft, library):
    names = {item["name"] for item in library["sounds"].values()}
    index = material_index(draft)
    found = []
    for track in draft["tracks"]:
        if track["type"] != "audio":
            continue
        for segment in track["segments"]:
            material = index.get(segment["material_id"], (None, {}))[1]
            if material.get("name") in names:
                found.append((segment, material))
    return found


def add_sfx(original, cues, library):
    if existing_saved_sfx(original, library):
        raise ValueError("Draft already contains a saved Favorite SFX; inspect before adding duplicates")
    target = copy.deepcopy(original)
    track_ends = []
    for cue in cues:
        slot = next((i for i, end in enumerate(track_ends) if cue["start"] >= end), None)
        if slot is None:
            slot = len(track_ends)
            track_ends.append(0)
            target["tracks"].append({"id": fresh_id(), "type": "audio", "segments": [],
                                     "flag": 0, "attribute": 0, "name": "", "is_default_name": True})
        track_ends[slot] = cue["start"] + cue["duration"]
        template = cue["template"]
        materials = template["materials"]
        refs = [template["segment"]["material_id"],
                *template["segment"].get("extra_material_refs", [])]
        index = {item["id"]: (kind, item) for kind, values in materials.items()
                 for item in values}
        ids = {old: fresh_id() for old in refs}
        for old in refs:
            kind, material = index[old]
            target["materials"][kind].append(remap(copy.deepcopy(material), ids))
        segment = remap(copy.deepcopy(template["segment"]), ids)
        segment["id"] = fresh_id()
        segment["target_timerange"]["start"] = cue["start"]
        segment["track_render_index"] = len(original["tracks"]) + slot
        segment["volume"] = cue["volume"]
        target["tracks"][len(original["tracks"]) + slot]["segments"].append(segment)
    validate_changes(original, target, cues)
    return target


def validate_changes(original, target, cues):
    if target["duration"] != original["duration"] or target["tracks"][:len(original["tracks"])] != original["tracks"]:
        raise ValueError("Existing timeline content changed")
    for kind, old_materials in original["materials"].items():
        if target["materials"][kind][:len(old_materials)] != old_materials:
            raise ValueError(f"Existing {kind} materials changed")
    index = material_index(target)
    new_tracks = target["tracks"][len(original["tracks"]):]
    if sum(len(track["segments"]) for track in new_tracks) != len(cues):
        raise ValueError("SFX cue count changed")
    for track_no, track in enumerate(new_tracks, len(original["tracks"])):
        end = 0
        for segment in track["segments"]:
            span = segment["target_timerange"]
            if span["start"] < end or span["duration"] <= 0:
                raise ValueError("SFX overlap or invalid duration")
            end = span["start"] + span["duration"]
            if end > target["duration"] or segment["track_render_index"] != track_no:
                raise ValueError("SFX exceeds draft or has wrong track index")
            for ref in [segment["material_id"], *segment.get("extra_material_refs", [])]:
                if ref not in index:
                    raise ValueError(f"Missing material reference {ref}")
            kind, material = index[segment["material_id"]]
            if kind != "audios" or not Path(material["path"]).is_file():
                raise ValueError(f"SFX media missing: {material.get('path')}")


def draft_files(project, draft):
    timeline = project / "Timelines" / draft["id"]
    content = [project / "draft_content.json", project / "template-2.tmp",
               timeline / "draft_content.json", timeline / "template-2.tmp"]
    backup = [*content, project / "draft_meta_info.json",
              project / "draft_cover.jpg", timeline / "draft_cover.jpg"]
    if not all(path.is_file() for path in backup):
        raise ValueError("Draft has missing root/timeline/cover files")
    if len({sha256(path) for path in content}) != 1:
        raise ValueError("Root/timeline content differs before editing")
    return content, backup


def capcut_running():
    if os.name != "nt":
        return False
    result = subprocess.run(["tasklist", "/FI", "IMAGENAME eq CapCut.exe", "/NH"],
                            capture_output=True, text=True, errors="replace")
    return "CapCut.exe" in result.stdout


def apply(project, target, metadata, backup_prefix="before-favorite-sfx"):
    if project.is_relative_to(project_root()) and capcut_running():
        raise ValueError("Save and close CapCut normally before writing the active draft")
    content, originals = draft_files(project, target)
    backup_dir = project / "_backup" / (backup_prefix + "-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    for path in originals:
        destination = backup_dir / path.relative_to(project)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
    encoded = json.dumps(target, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    json.loads(encoded)
    staged = []
    for path in content:
        temporary = path.with_name(path.name + ".capcut-sfx.tmp")
        temporary.write_bytes(encoded)
        staged.append((temporary, path))
    for temporary, path in staged:
        os.replace(temporary, path)
    metadata["tm_draft_modified"] = int(time.time() * 1_000_000)
    (project / "draft_meta_info.json").write_text(
        json.dumps(metadata, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    if len({sha256(path) for path in content}) != 1:
        raise ValueError("Root/timeline content differs after editing")
    return backup_dir


def verify(draft, library):
    effects = existing_saved_sfx(draft, library)
    failures = []
    if not 3 <= len(effects) <= 5:
        failures.append(f"Expected 3–5 SFX; found {len(effects)}")
    if not any(material["name"] in {library["sounds"][key]["name"] for key in KEYBOARDS}
               and segment["target_timerange"]["start"] == 0 for segment, material in effects):
        failures.append("No keyboard sound at the start")
    for segment, material in effects:
        if not Path(material["path"]).is_file():
            failures.append(f"Missing SFX file: {material['path']}")
        if segment["target_timerange"]["start"] + segment["target_timerange"]["duration"] > draft["duration"]:
            failures.append(f"SFX exceeds draft: {material['name']}")
    return {"valid": not failures, "sfx_count": len(effects),
            "effects": [{"name": material["name"],
                         "start_seconds": segment["target_timerange"]["start"] / 1_000_000}
                        for segment, material in effects], "failures": failures}


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["plan", "apply", "verify"])
    parser.add_argument("--name", required=True, help="Exact draft_meta_info.json draft_name")
    parser.add_argument("--plan", type=Path, help="JSON file with 3–5 cue placements")
    parser.add_argument("--project-dir", type=Path, help="Explicit draft directory, useful for an offline fixture")
    args = parser.parse_args()
    project, metadata = find_project(args.name, args.project_dir)
    original = read_json(project / "draft_content.json")
    library = read_json(LIBRARY)
    if args.action == "verify":
        result = verify(original, library)
    else:
        if not args.plan:
            parser.error("--plan is required for plan/apply")
        cues = parse_plan(args.plan, library, original["duration"])
        target = add_sfx(original, cues, library)
        result = {"valid": True, "draft": metadata["draft_name"],
                  "sfx_count": len(cues),
                  "effects": [{"sound": cue["key"], "start_seconds": cue["start"] / 1_000_000,
                               "duration_seconds": cue["duration"] / 1_000_000}
                              for cue in cues], "applied": args.action == "apply"}
        if args.action == "apply":
            result["backup"] = str(apply(project, target, metadata))
            checked = verify(read_json(project / "draft_content.json"), library)
            if not checked["valid"]:
                raise ValueError(f"Post-write verification failed: {checked['failures']}")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

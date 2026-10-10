#!/usr/bin/env python3
"""Prepare and install one-word subtitles in a CapCut desktop draft."""

from __future__ import annotations

import argparse
import copy
import csv
import difflib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time
import uuid
import wave
from datetime import datetime


DRAFT_FOLDER = pathlib.Path("CapCut/User Data/Projects/com.lveditor.draft")
TRACK_NAME = "Word subtitles"
MICROSECONDS = 1_000_000
WORD_SPLITS = {
    "ออกมา": ["ออก", "มา"],
    "มาจาก": ["มา", "จาก"],
    "เข้าไป": ["เข้า", "ไป"],
    "ให้ได้": ["ให้", "ได้"],
    "หลังจากนั้น": ["หลัง", "จาก", "นั้น"],
    "ได้มา": ["ได้", "มา"],
    "จากนั้น": ["จาก", "นั้น"],
    "ทำงานต่อ": ["ทำงาน", "ต่อ"],
    "ก็ได้": ["ก็", "ได้"],
    "เป็นช่วง": ["เป็น", "ช่วง"],
    "ทำเป็น": ["ทำ", "เป็น"],
    "แล้วก็": ["แล้ว", "ก็"],
    "อย่างเช่น": ["อย่าง", "เช่น"],
    "ไปดู": ["ไป", "ดู"],
    "ของจริง": ["ของ", "จริง"],
    "เป็นอัน": ["เป็น", "อัน"],
    "หลังจากที่": ["หลัง", "จาก", "ที่"],
    "ก่อนหน้านี้": ["ก่อน", "หน้า", "นี้"],
    "ใช้เวลา": ["ใช้", "เวลา"],
    "เวลาทำงาน": ["เวลา", "ทำงาน"],
    "แบบนี้": ["แบบ", "นี้"],
    "ทีนี้": ["ที", "นี้"],
    "ไม่ค่อย": ["ไม่", "ค่อย"],
    "ต่าง ๆ": ["ต่าง", "ต่าง"],
    "ง่าย ๆ": ["ง่าย", "ง่าย"],
    "จริง ๆ": ["จริง", "จริง"],
}


def read_json(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: pathlib.Path, value, *, indent: int | None = None):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=indent), encoding="utf-8")


def project_files(project: pathlib.Path):
    root = project / "draft_content.json"
    draft = read_json(root)
    timeline = project / "Timelines" / draft["id"]
    files = [root, project / "template-2.tmp", timeline / "draft_content.json", timeline / "template-2.tmp"]
    for path in files:
        if not path.is_file():
            raise ValueError(f"Missing active draft copy: {path}")
    copies = [read_json(path) for path in files]
    if any(item != draft for item in copies[1:]):
        raise ValueError("Root and active timeline copies differ; inspect them before writing")
    return draft, timeline, files


def default_roots():
    roots = []
    local = os.environ.get("LOCALAPPDATA")
    if local:
        roots.append(pathlib.Path(local) / "CapCut/User Data/Projects/com.lveditor.draft")
    users = pathlib.Path("C:/Users")
    if users.is_dir():
        roots.extend(user / "AppData/Local" / DRAFT_FOLDER for user in users.iterdir() if user.is_dir())
    return list(dict.fromkeys(root for root in roots if root.is_dir()))


def command_find(args):
    roots = [pathlib.Path(root) for root in args.root] if args.root else default_roots()
    hits = []
    for root in roots:
        for project in root.iterdir():
            meta = project / "draft_meta_info.json"
            if project.is_dir() and meta.is_file() and read_json(meta).get("draft_name") == args.name:
                hits.append(str(project.resolve()))
    print(json.dumps(hits, ensure_ascii=False, indent=2))
    if not hits:
        raise ValueError(f"No exact CapCut draft_name match: {args.name}")


def command_inspect(args):
    project = pathlib.Path(args.project).resolve()
    draft, timeline, _ = project_files(project)
    tracks = []
    for track in draft["tracks"]:
        tracks.append({"id": track["id"], "type": track["type"], "name": track.get("name", ""), "segments": len(track["segments"])})
    materials = {"videos": [], "audios": []}
    for kind in materials:
        for item in draft["materials"].get(kind, []):
            materials[kind].append({"id": item["id"], "name": item.get("material_name", item.get("name", "")), "type": item.get("type"), "path": item.get("path")})
    print(json.dumps({"project": str(project), "name": read_json(project / "draft_meta_info.json")["draft_name"], "duration_seconds": draft["duration"] / MICROSECONDS, "timeline": str(timeline), "tracks": tracks, "materials": materials}, ensure_ascii=False, indent=2))


def ffmpeg_path():
    found = shutil.which("ffmpeg")
    if found:
        return found
    local = os.environ.get("LOCALAPPDATA")
    if local:
        apps = pathlib.Path(local) / "CapCut/Apps"
        candidates = sorted(apps.glob("*/ffmpeg.exe")) if apps.is_dir() else []
        if candidates:
            return str(candidates[-1])
    raise ValueError("ffmpeg not found; pass a working ffmpeg on PATH")


def resolve_media(project: pathlib.Path, raw: str):
    value = raw.replace("\\", "/")
    match = re.match(r"^##_draftpath_placeholder_[^#]+_##/(.+)$", value)
    if match:
        return project / match.group(1)
    path = pathlib.Path(value)
    return path if path.is_absolute() else project / path


def has_audio(ffmpeg: str, path: pathlib.Path):
    result = subprocess.run([ffmpeg, "-hide_banner", "-i", str(path)], capture_output=True, text=True, errors="replace")
    return "Audio:" in result.stderr


def atempo_filters(ratio: float):
    if ratio <= 0:
        raise ValueError("Non-positive playback speed")
    filters = []
    while ratio > 2:
        filters.append("atempo=2")
        ratio /= 2
    while ratio < 0.5:
        filters.append("atempo=0.5")
        ratio /= 0.5
    if abs(ratio - 1) > 0.0001:
        filters.append(f"atempo={ratio:.8f}")
    return filters


def command_extract(args):
    project = pathlib.Path(args.project).resolve()
    draft, _, _ = project_files(project)
    tracks = [track for track in draft["tracks"] if track["type"] == "video" and track["segments"]]
    if args.track_id:
        tracks = [track for track in tracks if track["id"] == args.track_id]
    if not tracks:
        raise ValueError("No primary video track found")
    primary = max(tracks, key=lambda track: len(track["segments"]))
    if len(tracks) > 1 and not args.track_id:
        print("Warning: multiple video tracks; inspect whether another track contains speech", file=sys.stderr)
    ffmpeg = ffmpeg_path()
    videos = {item["id"]: item for item in draft["materials"].get("videos", [])}
    audios = {item["id"]: item for item in draft["materials"].get("audios", [])}
    paths, indexes, audio_cache = [], {}, {}

    def input_index(path: pathlib.Path):
        key = str(path.resolve())
        if key not in indexes:
            indexes[key] = len(paths)
            paths.append(path)
        return indexes[key]

    filters, labels = [], []
    cursor = 0
    segments = sorted(primary["segments"], key=lambda item: item["target_timerange"]["start"])
    for segment in segments:
        target = segment["target_timerange"]
        start, duration = target["start"], target["duration"]
        if start < cursor:
            raise ValueError("Overlapping primary video segments need manual extraction")
        if start > cursor:
            gap = (start - cursor) / MICROSECONDS
            label = f"[part{len(labels)}]"
            filters.append(f"anullsrc=r=16000:cl=mono,atrim=duration={gap:.6f}{label}")
            labels.append(label)
        cursor = start + duration
        if segment.get("reverse"):
            raise ValueError("Reverse playback needs manual audio extraction")
        material = videos[segment["material_id"]]
        path = resolve_media(project, material["path"])
        if not path.is_file():
            raise ValueError(f"Missing media: {path}")
        key = str(path.resolve())
        if key not in audio_cache:
            audio_cache[key] = has_audio(ffmpeg, path)
        seconds = duration / MICROSECONDS
        label = f"[part{len(labels)}]"
        if audio_cache[key]:
            source = segment["source_timerange"]
            source_seconds = source["duration"] / MICROSECONDS
            chain = [f"[{input_index(path)}:a]atrim=start={source['start']/MICROSECONDS:.6f}:duration={source_seconds:.6f}", "asetpts=PTS-STARTPTS", "aresample=16000", "aformat=channel_layouts=mono"]
            chain.extend(atempo_filters(source_seconds / seconds))
            chain.extend([f"apad=whole_dur={seconds:.6f}", f"atrim=duration={seconds:.6f}{label}"])
            filters.append(",".join(chain))
        else:
            filters.append(f"anullsrc=r=16000:cl=mono,atrim=duration={seconds:.6f}{label}")
        labels.append(label)
    if cursor < draft["duration"]:
        seconds = (draft["duration"] - cursor) / MICROSECONDS
        label = f"[part{len(labels)}]"
        filters.append(f"anullsrc=r=16000:cl=mono,atrim=duration={seconds:.6f}{label}")
        labels.append(label)
    filters.append("".join(labels) + f"concat=n={len(labels)}:v=0:a=1[primary]")

    overlays = []
    for track in draft["tracks"]:
        if track["type"] != "audio":
            continue
        for segment in track["segments"]:
            material = audios.get(segment["material_id"])
            if not material or material.get("type") != "record":
                continue
            path = resolve_media(project, material["path"])
            if not path.is_file():
                raise ValueError(f"Missing recorded audio: {path}")
            source, target = segment["source_timerange"], segment["target_timerange"]
            label = f"[voice{len(overlays)}]"
            filters.append(f"[{input_index(path)}:a]atrim=start={source['start']/MICROSECONDS:.6f}:duration={source['duration']/MICROSECONDS:.6f},asetpts=PTS-STARTPTS,aresample=16000,aformat=channel_layouts=mono,adelay={round(target['start']/1000)},apad=whole_dur={draft['duration']/MICROSECONDS:.6f}{label}")
            overlays.append(label)
    if overlays:
        filters.append("[primary]" + "".join(overlays) + f"amix=inputs={1+len(overlays)}:duration=first:dropout_transition=0[out]")
        output_label = "[out]"
    else:
        output_label = "[primary]"
    out = pathlib.Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y"]
    for path in paths:
        command.extend(["-i", str(path)])
    command.extend(["-filter_complex", ";".join(filters), "-map", output_label, "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(out)])
    subprocess.run(command, check=True)
    print(json.dumps({"audio": str(out), "primary_track": primary["id"], "record_overlays": len(overlays), "seconds": draft["duration"] / MICROSECONDS}, ensure_ascii=False))


def command_transcribe(args):
    try:
        import numpy as np
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise ValueError("Install faster-whisper and numpy in the chosen Python environment") from exc
    with wave.open(args.audio, "rb") as wav:
        if (wav.getnchannels(), wav.getframerate(), wav.getsampwidth()) != (1, 16000, 2):
            raise ValueError("Input must be mono 16 kHz PCM16 WAV from the extract command")
        audio = np.frombuffer(wav.readframes(wav.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    model = WhisperModel(args.model, device=args.device, compute_type=args.compute_type, cpu_threads=args.threads)
    segments, _ = model.transcribe(audio, language=args.language, beam_size=args.beam_size, initial_prompt=args.initial_prompt or None, word_timestamps=True, vad_filter=not args.no_vad, condition_on_previous_text=False)
    result = []
    for segment in segments:
        result.append({"start": segment.start, "end": segment.end, "text": segment.text, "words": [{"start": word.start, "end": word.end, "word": word.word, "probability": word.probability} for word in segment.words or []]})
        print(f"{segment.start:.2f}-{segment.end:.2f}", flush=True)
    write_json(pathlib.Path(args.out), result, indent=2)
    print(f"Wrote {len(result)} ASR segments to {args.out}")


def char_times(segment, corrected: str):
    chars = []
    for word in segment["words"]:
        start, end, value = word["start"], word["end"], word["word"]
        for index, char in enumerate(value):
            chars.append((char, start + (end-start)*index/max(1, len(value)), start + (end-start)*(index+1)/max(1, len(value))))
    raw = "".join(char for char, _, _ in chars)
    times = [None] * len(corrected)
    for operation, i1, i2, j1, j2 in difflib.SequenceMatcher(None, raw, corrected, autojunk=False).get_opcodes():
        if operation == "equal":
            for i, j in zip(range(i1, i2), range(j1, j2)):
                times[j] = (chars[i][1], chars[i][2])
        elif operation in ("replace", "insert") and j2 > j1:
            left = chars[i1][1] if i1 < len(chars) else segment["end"]
            right = chars[i2-1][2] if i2 > i1 else left
            if right <= left:
                left = chars[i1-1][2] if i1 > 0 else segment["start"]
                right = chars[i1][1] if i1 < len(chars) else segment["end"]
            if right <= left:
                right = left + 0.03 * (j2-j1)
            for j in range(j1, j2):
                times[j] = (left+(right-left)*(j-j1)/(j2-j1), left+(right-left)*(j-j1+1)/(j2-j1))
    return times


def command_wordify(args):
    try:
        from pythainlp.tokenize import word_tokenize
    except ImportError as exc:
        raise ValueError("Install pythainlp in the chosen Python environment") from exc
    raw = read_json(pathlib.Path(args.raw))
    corrected = read_json(pathlib.Path(args.corrected))
    if len(raw) != len(corrected):
        raise ValueError("Corrected text array must have one entry per raw ASR segment")
    captions = []
    for segment, phrase in zip(raw, corrected):
        phrase = (phrase["text"] if isinstance(phrase, dict) else phrase).strip()
        if not phrase:
            continue
        times = char_times(segment, phrase)
        cursor = 0
        for token in word_tokenize(phrase, engine="newmm"):
            if not token.strip():
                cursor += len(token)
                continue
            position = phrase.find(token, cursor)
            if position < 0:
                raise ValueError(f"Cannot align token {token!r} in phrase {phrase!r}")
            cursor = position + len(token)
            if re.fullmatch(r"[,.;:!?ฯ]", token):
                if captions:
                    captions[-1]["text"] += token
                continue
            spans = [value for value in times[position:cursor] if value]
            if not spans:
                continue
            start = max(segment["start"], min(value[0] for value in spans))
            end = min(segment["end"], max(value[1] for value in spans))
            if end <= start:
                end = min(segment["end"], start + 0.04)
            captions.append({"start": round(start, 3), "end": round(end, 3), "text": token})
    merged = []
    for caption in captions:
        if caption["text"] in ("%", "ๆ") and merged:
            merged[-1]["text"] += caption["text"]
            merged[-1]["end"] = caption["end"]
        else:
            merged.append(caption)
    expanded = []
    for caption in merged:
        parts = WORD_SPLITS.get(caption["text"])
        if not parts or caption["end"]-caption["start"] < 0.06*len(parts):
            expanded.append(caption)
            continue
        total = sum(len(part) for part in parts)
        at = caption["start"]
        for index, part in enumerate(parts):
            end = caption["end"] if index == len(parts)-1 else at+(caption["end"]-caption["start"])*len(part)/total
            expanded.append({"start": round(at, 3), "end": round(end, 3), "text": part})
            at = end
    captions = expanded
    for index, caption in enumerate(captions):
        if index and caption["start"] < captions[index-1]["end"]:
            midpoint = round((caption["start"]+captions[index-1]["end"])/2, 3)
            captions[index-1]["end"] = midpoint
            caption["start"] = midpoint
        if caption["end"] <= caption["start"]:
            caption["end"] = round(caption["start"]+0.033, 3)
    for index, caption in enumerate(captions):
        needed = 0.034-(caption["end"]-caption["start"])
        if needed <= 0:
            continue
        if index+1 < len(captions) and captions[index+1]["start"]-caption["end"] >= needed:
            caption["end"] = round(caption["end"]+needed, 3)
        elif index > 0 and captions[index-1]["end"]-captions[index-1]["start"] > needed+0.06:
            captions[index-1]["end"] = round(captions[index-1]["end"]-needed, 3)
            caption["start"] = round(caption["start"]-needed, 3)
    write_json(pathlib.Path(args.out), captions, indent=2)
    if args.tsv:
        with pathlib.Path(args.tsv).open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream, delimiter="\t")
            for caption in captions:
                writer.writerow([f"{caption['start']:.3f}", f"{caption['end']:.3f}", caption["text"]])
    print(json.dumps({"words": len(captions), "first": captions[0] if captions else None, "last": captions[-1] if captions else None}, ensure_ascii=False))


def is_live_project(project: pathlib.Path):
    return project.parent.name == "com.lveditor.draft" and project.parent.parent.name == "Projects"


def capcut_running():
    if os.name != "nt":
        return False
    result = subprocess.run(["tasklist", "/FI", "IMAGENAME eq CapCut.exe", "/NH"], capture_output=True, text=True, errors="replace")
    return "CapCut.exe" in result.stdout


def validate_captions(captions, duration: int):
    if not captions:
        raise ValueError("No captions supplied")
    last = 0
    for caption in captions:
        start = round(float(caption["start"])*MICROSECONDS)
        end = round(float(caption["end"])*MICROSECONDS)
        text = caption["text"]
        if not isinstance(text, str) or not text or any(char.isspace() for char in text):
            raise ValueError(f"Caption is not a single word: {text!r}")
        if start < last-1000 or end <= start or end > duration:
            raise ValueError(f"Invalid or overlapping caption time: {caption}")
        last = end


def command_apply(args):
    project = pathlib.Path(args.project).resolve()
    if is_live_project(project) and capcut_running():
        raise ValueError("Close CapCut before writing its live draft")
    meta_path = project / "draft_meta_info.json"
    meta = read_json(meta_path)
    if meta["draft_name"] != args.name:
        raise ValueError(f"Exact draft_name mismatch: {meta['draft_name']!r}")
    draft, timeline, files = project_files(project)
    captions = read_json(pathlib.Path(args.captions))
    validate_captions(captions, draft["duration"])
    if any(track.get("name") == TRACK_NAME for track in draft["tracks"]):
        raise ValueError(f"{TRACK_NAME!r} already exists; inspect before adding another track")
    donors = [track for track in draft["tracks"] if track["type"] == "text" and track["segments"]]
    if not donors:
        raise ValueError("No plain-text style in this draft; inspect a compatible CapCut draft for a donor style")
    donor_track = donors[-1]
    donor_segment = donor_track["segments"][-1]
    text_materials = {item["id"]: item for item in draft["materials"]["texts"]}
    donor_material = text_materials[donor_segment["material_id"]]
    if donor_material.get("type") != "text":
        raise ValueError("Chosen text donor is not plain text")
    track = copy.deepcopy(donor_track)
    track["id"] = str(uuid.uuid4()).upper()
    track["name"] = TRACK_NAME
    track["is_default_name"] = False
    track["segments"] = []
    render = max((segment.get("render_index", 0) for item in draft["tracks"] if item["type"] == "text" for segment in item["segments"]), default=14000) + 2
    track_render = max((segment.get("track_render_index", 0) for item in draft["tracks"] for segment in item["segments"]), default=0) + 1
    for caption in captions:
        word = caption["text"]
        material = copy.deepcopy(donor_material)
        material["id"] = str(uuid.uuid4()).upper()
        material["name"] = word
        content = json.loads(material["content"])
        content["text"] = word
        length = len(word.encode("utf-16-le")) // 2
        for style in content.get("styles", []):
            style["range"] = [0, length]
        if not content.get("styles"):
            raise ValueError("Donor text has no usable style")
        material["content"] = json.dumps(content, ensure_ascii=False, separators=(",", ":"))
        material["recognize_text"] = ""
        for key in ("words", "current_words"):
            if key in material:
                material[key] = {"start_time": [], "end_time": [], "text": []}
        draft["materials"]["texts"].append(material)
        segment = copy.deepcopy(donor_segment)
        segment["id"] = str(uuid.uuid4()).upper()
        segment["material_id"] = material["id"]
        start = round(float(caption["start"])*MICROSECONDS)
        duration = max(33333, round((float(caption["end"])-float(caption["start"]))*MICROSECONDS))
        segment["target_timerange"] = {"start": start, "duration": duration}
        segment["extra_material_refs"] = []
        segment["render_index"] = render
        segment["track_render_index"] = track_render
        segment["clip"]["transform"] = {"x": 0.0, "y": args.y}
        track["segments"].append(segment)
    draft["tracks"].append(track)
    backup = project / "_backup" / ("before-capcut-sub-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    for source in [*files, meta_path]:
        destination = backup / source.relative_to(project)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    encoded = json.dumps(draft, ensure_ascii=False, separators=(",", ":"))
    for path in files:
        staged = path.with_name(path.name + ".capcut-sub.tmp")
        staged.write_text(encoded, encoding="utf-8")
        read_json(staged)
        os.replace(staged, path)
    meta["tm_draft_modified"] = int(time.time()*MICROSECONDS)
    write_json(meta_path, meta)
    validate_project(project)
    print(json.dumps({"project": str(project), "words": len(captions), "backup": str(backup), "timeline": str(timeline)}, ensure_ascii=False))


def validate_project(project: pathlib.Path):
    draft, timeline, files = project_files(project)
    if len({path.read_bytes() for path in files}) != 1:
        raise ValueError("Root and timeline copies are not byte-identical")
    tracks = [track for track in draft["tracks"] if track.get("name") == TRACK_NAME]
    if len(tracks) != 1:
        raise ValueError(f"Expected one {TRACK_NAME!r} track, found {len(tracks)}")
    materials = {item["id"]: item for item in draft["materials"]["texts"]}
    last = 0
    for segment in tracks[0]["segments"]:
        target = segment["target_timerange"]
        start, end = target["start"], target["start"]+target["duration"]
        if start < last-1000 or end > draft["duration"]:
            raise ValueError("Caption time order or project duration invalid")
        last = end
        material = materials[segment["material_id"]]
        content = json.loads(material["content"])
        if content["text"] != material["name"] or any(char.isspace() for char in content["text"]):
            raise ValueError("Caption material text mismatch or multiple words")
    return {"project": str(project), "timeline": str(timeline), "words": len(tracks[0]["segments"]), "duration_seconds": draft["duration"]/MICROSECONDS}


def command_validate(args):
    print(json.dumps(validate_project(pathlib.Path(args.project).resolve()), ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    find = sub.add_parser("find", help="Find exact CapCut draft_name across local profiles")
    find.add_argument("--name", required=True)
    find.add_argument("--root", action="append", help="Optional draft-root directory; repeat to search several")
    find.set_defaults(func=command_find)
    inspect = sub.add_parser("inspect", help="Summarize active draft tracks and materials")
    inspect.add_argument("--project", required=True)
    inspect.set_defaults(func=command_inspect)
    extract = sub.add_parser("extract", help="Render edited primary-track speech to 16 kHz mono WAV")
    extract.add_argument("--project", required=True)
    extract.add_argument("--out", required=True)
    extract.add_argument("--track-id", help="Choose a video track when the draft has several")
    extract.set_defaults(func=command_extract)
    transcribe = sub.add_parser("transcribe", help="Run local faster-whisper with word timestamps")
    transcribe.add_argument("--audio", required=True)
    transcribe.add_argument("--out", required=True)
    transcribe.add_argument("--language", default="th")
    transcribe.add_argument("--model", default="turbo")
    transcribe.add_argument("--device", default="cpu")
    transcribe.add_argument("--compute-type", default="int8")
    transcribe.add_argument("--threads", type=int, default=8)
    transcribe.add_argument("--beam-size", type=int, default=5)
    transcribe.add_argument("--initial-prompt", default="")
    transcribe.add_argument("--no-vad", action="store_true", help="Keep quiet ranges for focused recovery passes")
    transcribe.set_defaults(func=command_transcribe)
    wordify = sub.add_parser("wordify", help="Align corrected Thai phrases to word timestamps")
    wordify.add_argument("--raw", required=True)
    wordify.add_argument("--corrected", required=True)
    wordify.add_argument("--out", required=True)
    wordify.add_argument("--tsv")
    wordify.set_defaults(func=command_wordify)
    apply = sub.add_parser("apply", help="Back up and insert a one-word text track into a closed draft")
    apply.add_argument("--project", required=True)
    apply.add_argument("--name", required=True)
    apply.add_argument("--captions", required=True)
    apply.add_argument("--y", type=float, default=-0.62, help="Vertical text transform copied to each word segment")
    apply.set_defaults(func=command_apply)
    validate = sub.add_parser("validate", help="Check synced draft copies and word track references")
    validate.add_argument("--project", required=True)
    validate.set_defaults(func=command_validate)
    args = parser.parse_args()
    try:
        args.func(args)
    except (KeyError, OSError, subprocess.CalledProcessError, ValueError, json.JSONDecodeError) as exc:
        parser.exit(1, f"capcut-sub: {exc}\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from typing import Any


LIST_FORMAT = (
    "#{session_name}\t#{window_index}\t#{pane_active}\t#{pane_id}\t"
    "#{pane_current_command}\t#{pane_tty}\t#{pane_current_path}\t#{pane_title}"
)


def fail(message: str, code: int = 1) -> "NoReturn":
    print(message, file=sys.stderr)
    raise SystemExit(code)


def ensure_tmux() -> None:
    if shutil.which("tmux") is None:
        fail("tmux is not installed or not on PATH")


def run_tmux(args: list[str]) -> str:
    ensure_tmux()
    try:
        result = subprocess.run(
            ["tmux", *args],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        message = exc.stderr.strip() or exc.stdout.strip() or "tmux command failed"
        fail(message)
    return result.stdout


def parse_list_output(raw: str) -> list[dict[str, object]]:
    panes: list[dict[str, object]] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) != 8:
            continue
        panes.append(
            {
                "session": parts[0],
                "window": parts[1],
                "active": parts[2] == "1",
                "pane_id": parts[3],
                "command": parts[4],
                "tty": parts[5],
                "path": parts[6],
                "title": parts[7],
            }
        )
    return panes


def capture_pane(pane: str) -> str:
    return run_tmux(["capture-pane", "-p", "-t", pane])


def sample_capture(capture: str, lines: int) -> dict[str, Any]:
    items = capture.splitlines()
    return {
        "line_count": len(items),
        "head": items[:lines],
        "tail": items[-lines:],
    }


def detect_codex_state(capture: str) -> dict[str, object]:
    lines = capture.splitlines()
    prompt_line = ""
    for line in reversed(lines):
        stripped = line.strip()
        if stripped.startswith("›"):
            prompt_line = stripped
            break

    looks_like_codex = any(
        token in capture
        for token in ("gpt-", "Context", "esc to interrupt", "Worked for", "codex")
    ) or bool(prompt_line)

    mode = "unknown"
    prompt_text = ""
    if "Working (" in capture:
        mode = "running"
    elif prompt_line:
        prompt_text = prompt_line[1:].strip()
        mode = "typed" if prompt_text else "idle"

    return {
        "looks_like_codex": looks_like_codex,
        "mode": mode,
        "prompt_text": prompt_text,
    }


def ensure_pane(pane: str) -> None:
    known = {item["pane_id"] for item in parse_list_output(run_tmux(["list-panes", "-a", "-F", LIST_FORMAT]))}
    if pane not in known:
        fail(f"unknown pane id: {pane}")


def cmd_list(_: argparse.Namespace) -> int:
    panes = parse_list_output(run_tmux(["list-panes", "-a", "-F", LIST_FORMAT]))
    print(json.dumps(panes, ensure_ascii=False, indent=2))
    return 0


def cmd_peek(args: argparse.Namespace) -> int:
    ensure_pane(args.pane)
    capture = capture_pane(args.pane)
    print(
        json.dumps(
            {
                "pane_id": args.pane,
                "sample": sample_capture(capture, args.lines),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def cmd_send_text(args: argparse.Namespace) -> int:
    ensure_pane(args.pane)
    run_tmux(["send-keys", "-t", args.pane, args.text])
    print(json.dumps({"pane_id": args.pane, "sent_text": args.text, "submitted": False}, ensure_ascii=False, indent=2))
    return 0


def cmd_send_keys(args: argparse.Namespace) -> int:
    ensure_pane(args.pane)
    run_tmux(["send-keys", "-t", args.pane, *args.keys])
    print(json.dumps({"pane_id": args.pane, "sent_keys": args.keys}, ensure_ascii=False, indent=2))
    return 0


def cmd_codex_state(args: argparse.Namespace) -> int:
    ensure_pane(args.pane)
    capture = capture_pane(args.pane)
    state = detect_codex_state(capture)
    state["pane_id"] = args.pane
    state["sample"] = sample_capture(capture, args.lines)
    print(json.dumps(state, ensure_ascii=False, indent=2))
    return 0


def cmd_codex_send(args: argparse.Namespace) -> int:
    ensure_pane(args.pane)
    run_tmux(["send-keys", "-t", args.pane, args.text])
    if args.submit:
        run_tmux(["send-keys", "-t", args.pane, "C-m"])
    capture = capture_pane(args.pane)
    state = detect_codex_state(capture)
    print(
        json.dumps(
            {
                "pane_id": args.pane,
                "sent_text": args.text,
                "submitted": bool(args.submit),
                "state": state,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Safe tmux helper for Codex skills")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List panes across all sessions")
    list_parser.set_defaults(func=cmd_list)

    peek_parser = subparsers.add_parser("peek", help="Capture a short sample from one pane")
    peek_parser.add_argument("--pane", required=True)
    peek_parser.add_argument("--lines", type=int, default=12)
    peek_parser.set_defaults(func=cmd_peek)

    text_parser = subparsers.add_parser("send-text", help="Send literal text to one pane")
    text_parser.add_argument("--pane", required=True)
    text_parser.add_argument("--text", required=True)
    text_parser.set_defaults(func=cmd_send_text)

    keys_parser = subparsers.add_parser("send-keys", help="Send one or more tmux key names")
    keys_parser.add_argument("--pane", required=True)
    keys_parser.add_argument("--keys", nargs="+", required=True)
    keys_parser.set_defaults(func=cmd_send_keys)

    state_parser = subparsers.add_parser("codex-state", help="Inspect likely Codex prompt state")
    state_parser.add_argument("--pane", required=True)
    state_parser.add_argument("--lines", type=int, default=12)
    state_parser.set_defaults(func=cmd_codex_state)

    codex_send_parser = subparsers.add_parser("codex-send", help="Send text to a Codex pane and optionally submit")
    codex_send_parser.add_argument("--pane", required=True)
    codex_send_parser.add_argument("--text", required=True)
    codex_send_parser.add_argument("--submit", action="store_true")
    codex_send_parser.set_defaults(func=cmd_codex_send)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

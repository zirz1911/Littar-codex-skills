#!/usr/bin/env python3
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import winreg
except ImportError:  # pragma: no cover
    winreg = None


REPO_DIR = Path(r"D:\Project\mcp-facebook-ads")
SERVER_PATH = REPO_DIR / "server.py"
PM2_APP_NAME = "facebook-ads"


def load_user_env(name: str) -> str | None:
    if os.getenv(name):
        return os.getenv(name)
    if winreg is None:
        return None
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as key:
            value, _ = winreg.QueryValueEx(key, name)
            return value.strip() if isinstance(value, str) and value.strip() else None
    except FileNotFoundError:
        return None
    except OSError:
        return None


def resolved_env() -> dict[str, str]:
    env = os.environ.copy()
    token = load_user_env("FB_ACCESS_TOKEN") or load_user_env("META_ACCESS_TOKEN")
    if token:
        env.setdefault("FB_ACCESS_TOKEN", token)
    ad_account_id = load_user_env("FB_AD_ACCOUNT_ID") or load_user_env("META_AD_ACCOUNT_ID")
    if ad_account_id:
        env.setdefault("FB_AD_ACCOUNT_ID", ad_account_id)
    env.setdefault("PYTHONUNBUFFERED", "1")
    return env


def require_credentials(env: dict[str, str]) -> None:
    if env.get("FB_ACCESS_TOKEN") or env.get("META_ACCESS_TOKEN"):
        return
    raise SystemExit("Missing FB_ACCESS_TOKEN or META_ACCESS_TOKEN")


def pm2_path() -> str:
    path = shutil.which("pm2") or shutil.which("pm2.cmd")
    if not path:
        raise SystemExit("pm2 not found in PATH")
    return path


def run(cmd: list[str], env: dict[str, str] | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(REPO_DIR),
        env=env,
        check=check,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
    )


def pm2_jlist(env: dict[str, str]) -> list[dict]:
    result = run([pm2_path(), "jlist"], env=env)
    stdout = result.stdout.strip()
    if not stdout:
        return []
    try:
        return json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Failed to parse pm2 jlist output: {exc}") from exc


def pm2_status(env: dict[str, str]) -> dict:
    for app in pm2_jlist(env):
        if app.get("name") == PM2_APP_NAME:
            pm2_env = app.get("pm2_env", {})
            return {
                "found": True,
                "status": pm2_env.get("status"),
                "pid": app.get("pid"),
                "pm_id": app.get("pm_id"),
                "cwd": pm2_env.get("pm_cwd"),
            }
    return {"found": False, "status": "missing"}


def ensure_running(env: dict[str, str]) -> dict:
    require_credentials(env)
    status = pm2_status(env)
    if status["found"] and status["status"] == "online":
        return {"ok": True, "status": status, "started": False}

    run([pm2_path(), "start", "ecosystem.config.js", "--only", PM2_APP_NAME, "--update-env"], env=env)
    status = pm2_status(env)
    if not status["found"] or status["status"] != "online":
        raise SystemExit(f"Failed to start pm2 app {PM2_APP_NAME}")
    return {"ok": True, "status": status, "started": True}


def server_roundtrip(payload: dict, env: dict[str, str]) -> dict:
    require_credentials(env)
    if not SERVER_PATH.exists():
        raise SystemExit(f"Server not found: {SERVER_PATH}")
    process = subprocess.run(
        [sys.executable, str(SERVER_PATH)],
        cwd=str(REPO_DIR),
        env=env,
        input=json.dumps(payload) + "\n",
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=True,
    )
    stdout = process.stdout.strip()
    if not stdout:
        raise SystemExit("MCP server returned no output")
    first_line = stdout.splitlines()[0]
    try:
        return json.loads(first_line)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Failed to parse MCP response: {exc}\nRaw: {first_line}") from exc


def cmd_status(_: argparse.Namespace) -> int:
    env = resolved_env()
    status = pm2_status(env)
    print(json.dumps({
        "repo_dir": str(REPO_DIR),
        "server_exists": SERVER_PATH.exists(),
        "has_token": bool(env.get("FB_ACCESS_TOKEN") or env.get("META_ACCESS_TOKEN")),
        "pm2": status,
    }, indent=2))
    return 0


def cmd_ensure_running(_: argparse.Namespace) -> int:
    env = resolved_env()
    print(json.dumps(ensure_running(env), indent=2))
    return 0


def cmd_tools_list(_: argparse.Namespace) -> int:
    env = resolved_env()
    ensure_running(env)
    response = server_roundtrip({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}, env)
    print(json.dumps(response, indent=2))
    return 0


def cmd_call(args: argparse.Namespace) -> int:
    env = resolved_env()
    ensure_running(env)
    arguments = {}
    raw_arguments = None
    if args.arguments_stdin:
        raw_arguments = sys.stdin.read()
    elif args.arguments_file:
        raw_arguments = Path(args.arguments_file).read_text(encoding="utf-8")
    elif args.arguments:
        raw_arguments = args.arguments

    if raw_arguments:
        try:
            arguments = json.loads(raw_arguments)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid JSON in tool arguments: {exc}") from exc
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": args.tool,
            "arguments": arguments,
        },
    }
    response = server_roundtrip(payload, env)
    print(json.dumps(response, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Facebook Ads MCP helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    status_parser = subparsers.add_parser("status", help="Show repo, token, and pm2 status")
    status_parser.set_defaults(func=cmd_status)

    ensure_parser = subparsers.add_parser("ensure-running", help="Start PM2 app if not online")
    ensure_parser.set_defaults(func=cmd_ensure_running)

    tools_parser = subparsers.add_parser("tools-list", help="List MCP tools")
    tools_parser.set_defaults(func=cmd_tools_list)

    call_parser = subparsers.add_parser("call", help="Call MCP tool")
    call_parser.add_argument("--tool", required=True, help="Tool name")
    call_parser.add_argument("--arguments", help="JSON object string for tool arguments")
    call_parser.add_argument("--arguments-file", help="Path to JSON file for tool arguments")
    call_parser.add_argument("--arguments-stdin", action="store_true", help="Read JSON arguments from stdin")
    call_parser.set_defaults(func=cmd_call)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Reload GemPhoneFarm UI window after workflow changes.

Tries CDP first (Electron remote debugging), falls back to
AppleScript (macOS) or PowerShell (Windows) keyboard shortcut.
"""

import json
import os
import subprocess
import sys
import urllib.request


def reload_via_cdp():
    """Try Chrome DevTools Protocol on common ports."""
    for port in [9222, 9223, 9225, 8315]:
        try:
            r = urllib.request.urlopen(
                f"http://localhost:{port}/json/list", timeout=2
            )
            pages = json.loads(r.read())
        except Exception:
            continue

        target = None
        for p in pages:
            url = p.get("url", "")
            title = p.get("title", "")
            if "localhost:1256" in url or (
                "DevTools" not in title and "GemPhoneFarm" in title
            ):
                target = p
                break

        if not target and pages:
            # Pick first non-DevTools page
            for p in pages:
                if "DevTools" not in p.get("title", ""):
                    target = p
                    break

        if target:
            try:
                import websocket
                ws = websocket.create_connection(
                    target["webSocketDebuggerUrl"], timeout=5
                )
                ws.send(
                    json.dumps(
                        {
                            "id": 1,
                            "method": "Runtime.evaluate",
                            "params": {"expression": "location.reload()"},
                        }
                    )
                )
                ws.recv()
                ws.close()
                print("OK")
                return True
            except Exception as e:
                print(f"CDP_WS_FAIL port={port}: {e}", file=sys.stderr)
                continue

    return False


def reload_via_applescript():
    """Send Cmd+R to GemPhoneFarm via AppleScript."""
    script = '''
tell application "GemPhoneFarm" to activate
delay 0.35
tell application "System Events"
    keystroke "r" using command down
end tell
'''
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=3,
        )
    except subprocess.TimeoutExpired:
        print("APPLESCRIPT_TIMEOUT", file=sys.stderr)
        return False
    except Exception as e:
        print(f"APPLESCRIPT_FAIL {e}", file=sys.stderr)
        return False

    if result.returncode == 0:
        print("OK")
        return True

    err = (result.stderr or result.stdout or "").strip()
    print(f"APPLESCRIPT_FAIL exit={result.returncode} {err}", file=sys.stderr)
    return False


def reload_via_windows():
    """Send Ctrl+R to GemPhoneFarm via PowerShell."""
    ps1 = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "reload_gemphonefarm.ps1")
    if not os.path.exists(ps1):
        print("POWERSHELL_NO_SCRIPT", file=sys.stderr)
        return False
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
             "-File", ps1],
            capture_output=True,
            text=True,
            timeout=8,
        )
    except Exception as e:
        print(f"POWERSHELL_FAIL {e}", file=sys.stderr)
        return False

    if result.returncode == 0 and "OK" in (result.stdout or ""):
        print("OK")
        return True

    err = (result.stderr or result.stdout or "").strip()
    print(f"POWERSHELL_FAIL exit={result.returncode} {err}", file=sys.stderr)
    return False


def reload_gemphonefarm():
    if reload_via_cdp():
        return True
    if sys.platform == "darwin":
        return reload_via_applescript()
    if sys.platform.startswith("win"):
        return reload_via_windows()
    print("UNSUPPORTED_PLATFORM", file=sys.stderr)
    return False


if __name__ == "__main__":
    ok = reload_gemphonefarm()
    sys.exit(0 if ok else 1)

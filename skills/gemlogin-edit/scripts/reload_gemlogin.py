import json
import os
import subprocess
import sys
import urllib.request

import websocket


def reload_via_cdp():
    try:
        r = urllib.request.urlopen("http://localhost:9222/json/list", timeout=3)
        pages = json.loads(r.read())
    except Exception as e:
        print("CDP_LIST_FAIL", e)
        return False

    target = None
    for p in pages:
        url = p.get("url", "")
        title = p.get("title", "")
        if "localhost:1010" in url or ("DevTools" not in title and title.startswith("GemLogin")):
            target = p
            break

    if not target:
        for p in pages:
            if "DevTools" not in p.get("title", "") and len(p.get("title", "")) > 0:
                target = p
                break

    if not target:
        print("NOT_FOUND")
        return False

    try:
        ws = websocket.create_connection(target["webSocketDebuggerUrl"], timeout=5)
        ws.send(
            json.dumps(
                {
                    "id": 1,
                    "method": "Runtime.evaluate",
                    "params": {"expression": "location.reload()"},
                }
            )
        )
        resp = ws.recv()
        ws.close()
        data = json.loads(resp)
        if "result" in data and "result" in data["result"]:
            print("OK")
            return True
        print("CDP_ERROR", resp)
        return False
    except Exception as e:
        print("CDP_WS_FAIL", e)
        return False


def reload_via_applescript():
    script = """
tell application "GemLogin" to activate
delay 0.35
tell application "System Events"
    keystroke "r" using command down
end tell
"""
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=3,
        )
    except Exception as e:
        print("APPLESCRIPT_FAIL", "Accessibility permission or AppleScript timeout:", e)
        return False

    if result.returncode == 0:
        print("APPLESCRIPT_OK")
        return True

    err = (result.stderr or result.stdout or "").strip()
    print("APPLESCRIPT_FAIL", err or f"exit={result.returncode}")
    return False


def reload_via_windows():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ps1 = os.path.join(script_dir, "reload_gemlogin.ps1")
    powershell = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        ps1,
    ]
    try:
        result = subprocess.run(
            powershell,
            capture_output=True,
            text=True,
            timeout=8,
        )
    except Exception as e:
        print("POWERSHELL_FAIL", e)
        return False

    out = (result.stdout or "").strip()
    err = (result.stderr or "").strip()
    if result.returncode == 0 and "OK" in out:
        print("POWERSHELL_OK")
        return True

    print("POWERSHELL_FAIL", err or out or f"exit={result.returncode}")
    return False


def reload_gemlogin():
    if reload_via_cdp():
        return True
    if sys.platform == "darwin":
        return reload_via_applescript()
    if sys.platform.startswith("win"):
        return reload_via_windows()
    print("UNSUPPORTED_FALLBACK", sys.platform)
    return False


if __name__ == "__main__":
    ok = reload_gemlogin()
    sys.exit(0 if ok else 1)

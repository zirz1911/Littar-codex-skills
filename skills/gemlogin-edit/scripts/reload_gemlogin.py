import urllib.request
import json
import websocket
import sys

def reload_gemlogin():
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
        # Match GemLogin main window (not DevTools), prefer localhost:1010
        if "localhost:1010" in url or ("DevTools" not in title and title.startswith("GemLogin")):
            target = p
            break

    if not target:
        # fallback: any non-DevTools page
        for p in pages:
            if "DevTools" not in p.get("title", "") and len(p.get("title", "")) > 0:
                target = p
                break

    if not target:
        print("NOT_FOUND")
        return False

    try:
        ws = websocket.create_connection(target["webSocketDebuggerUrl"], timeout=5)
        ws.send(json.dumps({
            "id": 1,
            "method": "Runtime.evaluate",
            "params": {"expression": "location.reload()"}
        }))
        resp = ws.recv()
        ws.close()
        data = json.loads(resp)
        if "result" in data and "result" in data["result"]:
            print("OK")
            return True
        else:
            print("CDP_ERROR", resp)
            return False
    except Exception as e:
        print("CDP_WS_FAIL", e)
        return False

if __name__ == "__main__":
    ok = reload_gemlogin()
    sys.exit(0 if ok else 1)

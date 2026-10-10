#!/usr/bin/env python3
"""Capture and verify selector evidence from a live Chromium CDP page."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

try:
    import websocket
except ImportError as exc:  # pragma: no cover - environment dependency
    raise SystemExit("Install websocket-client: python3 -m pip install websocket-client") from exc


INSPECT_JS = r"""
(function (spec) {
  function visible(el) {
    const s = getComputedStyle(el), r = el.getBoundingClientRect();
    return s.display !== 'none' && s.visibility !== 'hidden' &&
      r.width > 0 && r.height > 0;
  }
  function xpath(el) {
    if (el.id) return `//*[@id=${JSON.stringify(el.id)}]`;
    const parts = [];
    while (el && el.nodeType === 1) {
      let i = 1, sib = el.previousElementSibling;
      while (sib) { if (sib.tagName === el.tagName) i++; sib = sib.previousElementSibling; }
      parts.unshift(`${el.tagName.toLowerCase()}[${i}]`);
      el = el.parentElement;
    }
    return '/' + parts.join('/');
  }
  function css(el) {
    for (const attr of ['data-testid', 'aria-label', 'name', 'placeholder']) {
      const value = el.getAttribute(attr);
      if (value) return `${el.tagName.toLowerCase()}[${attr}=${JSON.stringify(value)}]`;
    }
    return null;
  }
  function matches() {
    if (spec.css) return [...document.querySelectorAll(spec.css)];
    if (spec.xpath) {
      const result = document.evaluate(spec.xpath, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
      return Array.from({length: result.snapshotLength}, (_, i) => result.snapshotItem(i));
    }
    let nodes = [...document.querySelectorAll('button, a, input, textarea, select, [role], [contenteditable="true"]')];
    if (spec.text) nodes = nodes.filter(el => (el.innerText || el.value || '').trim().includes(spec.text));
    if (spec.role) nodes = nodes.filter(el => el.getAttribute('role') === spec.role || (spec.role === 'button' && el.tagName === 'BUTTON'));
    if (spec.ariaLabel) nodes = nodes.filter(el => el.getAttribute('aria-label') === spec.ariaLabel);
    return nodes;
  }
  const elements = matches().filter(Boolean);
  return {
    url: location.href,
    title: document.title,
    selector: spec,
    matches: elements.map(el => ({
      xpath: xpath(el), css: css(el), tag: el.tagName.toLowerCase(),
      role: el.getAttribute('role'), aria_label: el.getAttribute('aria-label'),
      text: (el.innerText || el.value || '').trim().slice(0, 200),
      match_count: elements.length, visible: visible(el),
      enabled: !el.disabled, clickable: visible(el) && !el.disabled
    }))
  };
})(SPEC)
"""


def cdp_targets(address: str) -> list[dict]:
    parsed = urllib.parse.urlparse(address if "://" in address else f"http://{address}")
    base = f"http://{parsed.netloc}"
    with urllib.request.urlopen(f"{base}/json/list", timeout=5) as response:
        return json.load(response)


def evaluate(target: dict, expression: str) -> dict:
    ws = websocket.create_connection(target["webSocketDebuggerUrl"], timeout=10)
    try:
        ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {
            "expression": expression, "returnByValue": True, "awaitPromise": True
        }}))
        while True:
            message = json.loads(ws.recv())
            if message.get("id") != 1:
                continue
            if "exceptionDetails" in message.get("result", {}):
                raise RuntimeError(message["result"]["exceptionDetails"])
            return message["result"]["result"].get("value", {})
    finally:
        ws.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--debugger-address", required=True, help="CDP address, e.g. 127.0.0.1:9222")
    parser.add_argument("--name", required=True, help="Logical selector name")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--css")
    group.add_argument("--xpath")
    group.add_argument("--text")
    group.add_argument("--role")
    group.add_argument("--aria-label", dest="aria_label")
    parser.add_argument("--output", help="Optional JSON output path")
    args = parser.parse_args()

    targets = [t for t in cdp_targets(args.debugger_address) if t.get("type") == "page" and t.get("webSocketDebuggerUrl")]
    if not targets:
        raise SystemExit("No CDP page target found")
    target = next((t for t in targets if "devtools" not in t.get("title", "").lower()), targets[0])
    spec = {"css": args.css, "xpath": args.xpath, "text": args.text,
            "role": args.role, "ariaLabel": args.aria_label}
    spec = {key: value for key, value in spec.items() if value is not None}
    result = evaluate(target, INSPECT_JS.replace("SPEC", json.dumps(spec)))
    artifact = {"captured_at": datetime.now(timezone.utc).isoformat(), "name": args.name, **result}
    output = json.dumps(artifact, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as file:
            file.write(output + "\n")
    print(output)
    return 0 if artifact["matches"] else 1


if __name__ == "__main__":
    sys.exit(main())

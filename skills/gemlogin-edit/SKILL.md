---
name: gemlogin-edit
description: Directly modify GemLogin workflows via its local SQLite database. Use when user asks to edit, batch update, rename, or change workflow logic in GemLogin by manipulating the db.db file directly.
---
# gemlogin-edit Skill

Directly modify GemLogin workflows via its local SQLite database.

## Path
Database: `C:\Users\pajipan\.gemlogin\db.db`
Workflows Table: `apps`
Reload Script: `scripts\reload_gemlogin.py` (bundled with this skill)

## Capability
- List all internal workflows.
- Read JSON structure of a specific workflow from the `script` column.
- Update workflow logic (nodes, urls, parameters) by rewriting JSON back to `db.db`.
- Rename workflows.
- Delete workflows.
- Auto-reload GemLogin UI after every database write.

## Rules
1. **Always Backup**: Copy `db.db` before writing any changes.
2. **JSON Integrity**: Validate JSON structure before updating.
3. **Mandatory Reload UI**: After every database write (update, rename, delete), trigger GemLogin UI reload automatically. Use the bundled Python script (`scripts\reload_gemlogin.py`). It connects to GemLogin Chrome DevTools Protocol (CDP) on port 9222 and runs `location.reload()` directly. If CDP is unavailable, fall back to instructing the user to open DevTools (F12) and run `location.reload()`. Reload is NOT optional -- every write must be followed by a reload.
4. **Target IDs**: Use consistent node IDs (e.g., `open-url-node`) for easier automation.
5. **Read Real Shape First**: In GemLogin workflow JSON, actual block flow usually lives in `script -> drawflow -> nodes` and `script -> drawflow -> edges`. Do not assume `nodes` / `edges` exist at top level.
6. **Block Kind vs Node Type**: Many executable nodes have generic `type: "BlockBasicWithFallback"`. Real block kind is often in `label` such as `event-click`, `clipboard`, `command`, `file-action`, `press-key`, `element-scroll`.
7. **Prefer Built-in Blocks Over JS**: If user intent can be expressed with existing GemLogin blocks, use them instead of adding custom JavaScript. Only use JS when built-in blocks cannot express required behavior cleanly.
8. **Clipboard Limitation**: GemLogin `clipboard` block is not supported in background execution. If workflow depends on `clipboard` type `get`, keep it on popup / web execution path.
9. **Read Whole Graph Before Patching**: Inspect both node data and edge routing before changing behavior. Do not assume UI symptoms are only selector problems.
10. **Single Submit Source**: If a path uses `press-key Enter` as submit, remove or neutralize duplicate JS submit behavior on that same path.
11. **Layout Is Part Of Maintenance**: When fallback logic grows, keep `MAIN PATH` and `FALLBACK PATH` visually separated in editor and update note blocks after logic changes.
12. **Conditions Need Upstream Context**: Do not explain or patch a `conditions` block in isolation. First find which earlier node sets the variable that drives the branch.
13. **Label Stable Edges**: After workflow behavior stabilizes, add short edge labels for main branches and fallback branches so the graph explains intent without opening every node.
14. **Trigger Params Need Dual Sync**: When adding or changing manual trigger parameters, update both `script -> trigger -> parameters` and `script -> drawflow -> nodes[trigger-node] -> data -> parameters`. Updating only one side can leave GemLogin UI or external tool discovery out of sync.
15. **Post Confirmation Is Separate Step**: For TikTok Studio posting flows, treat first `Post` click and follow-up `Post now` modal as separate nodes with explicit detection and branching. Do not assume one click is enough.
16. **String Input Migration Changes Loop Semantics**: When replacing `read-file-text` inputs with manual `string` parameters, inspect every edge that loops back into the old reader. A direct string input often needs a one-shot loader or branch retarget to `end-node`; otherwise the workflow can reprocess the same value forever.
17. **Condition Handles Must Match Condition IDs**: If a `conditions` branch visually exists but runtime shows `nextBlockId = null`, inspect each outgoing edge `sourceHandle`. It must match the exact condition id pattern like `<node-id>-output-cond-share-repost`.
18. **Loop Breakpoint Needs Real Shape**: A valid loop breakpoint needs matching `type: "BlockLoopBreakpoint"`, `label: "loop-breakpoint"`, and coherent `data` such as `loopId`. Changing only `type` can leave a fake block in editor.
19. **One Return Path Per Loop**: In loop-heavy workflows, route all action branches back into one shared `scroll -> pause -> loop-breakpoint` chain unless behavior truly differs. Separate mini-loops become hard to debug and easy to break.
20. **Stale UI State Matters Across Iterations**: Before assuming selector or form failure, check whether previous loop left modal, panel, or toggle state open. Sometimes fix belongs in loop cleanup, not failing block itself.

## Scripts
- `scripts/reload_gemlogin.py` -- CDP-based reload. Connects to `localhost:9222`, finds the GemLogin page, and executes `location.reload()` over the DevTools protocol.
- `scripts/reload_gemlogin.ps1` -- Legacy keyboard fallback. Focuses the GemLogin window and sends `Ctrl+R`.
- `scripts/create_test_reload.py` -- Inserts a minimal test workflow named `DevTools Test Reload` into `db.db`.

## Automation Script Template
Use Python to interact with the database and auto-reload the UI.

```python
import sqlite3, json, os, shutil, subprocess, sys
from datetime import datetime

DB_PATH = r"C:\Users\pajipan\.gemlogin\db.db"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RELOAD_PY = os.path.join(SCRIPT_DIR, "scripts", "reload_gemlogin.py")

def backup_db():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = DB_PATH.replace(".db", f"_bk_{ts}.db")
    shutil.copy2(DB_PATH, backup)
    return backup

def reload_gemlogin_ui():
    if not os.path.exists(RELOAD_PY):
        print("[reload] Script not found. Open GemLogin DevTools (F12) and run location.reload()")
        return
    try:
        result = subprocess.run(
            [sys.executable, RELOAD_PY],
            capture_output=True, text=True, timeout=10
        )
        out = result.stdout.strip()
        if out == "OK":
            print("[reload] GemLogin UI reloaded.")
        elif out == "NOT_FOUND":
            print("[reload] GemLogin page not found. Open DevTools (F12) and run location.reload()")
        else:
            print("[reload] Unexpected output:", out, result.stderr)
    except Exception as e:
        print("[reload] Error:", e)

def list_workflows():
    conn = sqlite3.connect(DB_PATH)
    res = conn.execute("SELECT id, name FROM apps").fetchall()
    conn.close()
    return res

def get_workflow(name):
    conn = sqlite3.connect(DB_PATH)
    res = conn.execute("SELECT script FROM apps WHERE name = ?", (name,)).fetchone()
    conn.close()
    return json.loads(res[0]) if res else None

def update_workflow(name, workflow_dict, new_name=None):
    backup_db()
    conn = sqlite3.connect(DB_PATH)
    new_script = json.dumps(workflow_dict, ensure_ascii=False)
    target_name = new_name if new_name else name
    conn.execute("UPDATE apps SET script = ?, name = ?, updatedAt = datetime('now') WHERE name = ?",
                 (new_script, target_name, name))
    conn.commit()
    conn.close()
    reload_gemlogin_ui()  # MANDATORY

def delete_workflow(name):
    backup_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM apps WHERE name = ?", (name,))
    conn.commit()
    conn.close()
    reload_gemlogin_ui()  # MANDATORY
```

## DB Shape Notes
- Workflow JSON from `apps.script` is not flat. Inspect `workflow_dict["drawflow"]["nodes"]` and `workflow_dict["drawflow"]["edges"]`.
- `nodes` is an array, not always an object map. Build your own `node_map = {node["id"]: node for node in nodes}` when patching.
- Edges use node-handle strings like `<node-id>-input-1`, `<node-id>-output-1`, or `<node-id>-output-fallback`.
- `conditions` outputs commonly use handles like `<node-id>-output-cond-<condition-id>`.
- For many blocks, `label` is more reliable than `type` when identifying what the node actually does.
- Edge `label` is useful operational metadata. Use it to explain outcome or routing, not to repeat full node descriptions.

## Verified Block Schemas
These fields were verified from live workflow data in `db.db`, including `[TikTok] Like comment share`.

### Clipboard block
- Typical node shape:

```json
{
  "type": "BlockBasicWithFallback",
  "label": "clipboard",
  "data": {
    "icon": "riClipboardLine",
    "disableBlock": false,
    "description": "",
    "type": "get",
    "assignVariable": true,
    "variableName": "comment_link_url",
    "saveData": false,
    "dataColumn": "",
    "dataToCopy": "",
    "copySelectedText": false,
    "delay": 400
  }
}
```

- Runtime behavior from bundled app code:
  - `type: "get"` reads clipboard text.
  - If `assignVariable` is true, result is stored to `variableName`.
  - If `saveData` is true, result is inserted into `dataColumn`.
  - `clipboard` block is not supported in background execution.

### Command block
- Typical node shape:

```json
{
  "type": "BlockBasicWithFallback",
  "label": "command",
  "data": {
    "icon": "riTerminalBoxLine",
    "command": "powershell ...",
    "regex": "",
    "variableName": "",
    "assignVariable": false,
    "delay": 200,
    "description": ""
  }
}
```

### File Action block
- Typical append-write shape:

```json
{
  "type": "BlockBasicWithFallback",
  "label": "file-action",
  "data": {
    "icon": "riFileTextLine",
    "disableBlock": false,
    "action": "Write",
    "filePath": "{{variables.output_path}}",
    "inputData": "{{variables.output_value}}",
    "delimiter": "",
    "selectorType": "txt",
    "writeMode": "append",
    "appendMode": "newLine",
    "deleteFileFolder": "",
    "delay": 0
  }
}
```

### Event Click block
- Typical node shape:

```json
{
  "type": "BlockBasicWithFallback",
  "label": "event-click",
  "data": {
    "icon": "riCursorLine",
    "disableBlock": false,
    "description": "",
    "x": "",
    "y": "",
    "findBy": "xpath",
    "waitForSelector": true,
    "waitSelectorTimeout": 15000,
    "selector": "//*[@example='selector']",
    "markEl": false,
    "multiple": false,
    "selectOption": "leftClick",
    "delay": 1500,
    "humanClick": true
  }
}
```

### Conditions block
- Typical node shape:

```json
{
  "type": "BlockConditions",
  "label": "conditions",
  "data": {
    "icon": "riAB",
    "description": "Main router. valid -> open, skip -> read next, eof -> end.",
    "disableBlock": false,
    "conditions": [
      {
        "id": "cond-valid",
        "name": "Link valid",
        "conditions": [
          {
            "id": "group-valid",
            "conditions": [
              {
                "id": "rule-valid",
                "items": [
                  { "type": "value", "category": "value", "data": { "value": "{{variables.line_state}}" } },
                  { "category": "compare", "type": "eq" },
                  { "type": "value", "category": "value", "data": { "value": "valid" } }
                ]
              }
            ]
          }
        ]
      }
    ],
    "retryConditions": false,
    "retryCount": 10,
    "retryTimeout": 1000,
    "delay": 0
  }
}
```

- Read this block in 4 parts:
  - upstream node that sets branch variable
  - branch definitions inside `data.conditions`
  - outgoing edges by `sourceHandle`
  - downstream target nodes

### Loop Breakpoint block
- Typical node shape:

```json
{
  "type": "BlockLoopBreakpoint",
  "label": "loop-breakpoint",
  "data": {
    "icon": "riStopLine",
    "loopId": "warm-loop",
    "clearLoop": false,
    "$breakpoint": false
  }
}
```

- Common pitfall:
  - setting `type` to `BlockLoopBreakpoint` while leaving `label` or `data` from another block type
  - editor then shows odd placeholder block instead of real loop breakpoint

### Note block
- Typical node shape:

```json
{
  "type": "BlockNote",
  "label": "note",
  "data": {
    "icon": "riFileEditLine",
    "disableBlock": false,
    "note": "SECTION TITLE\nShort workflow note",
    "drawing": false,
    "width": 960,
    "height": 110,
    "color": "green",
    "fontSize": "large"
  }
}
```

- Use note blocks for:
  - section headers like `SETUP`, `COMMENT`, `SCROLL + LOOP`
  - short operator guidance
  - separating main flow from recovery flow without opening every node

## Verified Workflow Pattern: line-state router
Observed from `[TikTok] Like comment share` in `db.db`:

- Upstream JS node `parse-links-node` sets `line_state` to:
  - `valid`
  - `skip`
  - `eof`
- `loop-links-node` then routes by conditions on `{{variables.line_state}}`
- Outgoing handles map branch-to-edge:
  - `loop-links-node-output-cond-valid` -> `open-url-node`
  - `loop-links-node-output-cond-skip` -> `read-links-node`
  - `loop-links-node-output-cond-eof` -> `end-node`
- Short edge labels make this readable in editor:
  - `Open URL`
  - `Skip line`
  - `No more link`

## Verified Workflow Pattern: TikTok comment link capture
Observed from `[TikTok] Like comment share` in `db.db` and aligned with the latest wrap at `D:\Littar-Codex\Kvasir\memory\retrospectives\2026-06\05\09.45_gemlogin_tiktok_workflow_stabilization.md`.

- Trigger parameters:
  - `links_file`
  - `comment_file`
  - `comment_link_file`
- Main comment submit path:
  - `Fill Comment -> Presskey Enter`
  - Keep submit source-of-truth in one place. Do not leave JS submit active in parallel with `press-key`.
- Main comment-link capture path after submit:
  - `event-click` on comment timestamp
  - `clipboard` with `type: "get"` and `assignVariable: true`
  - `command` or `file-action` to append stored variable into text file
- Concrete example used in workflow:
  - `comment-copy-link-node` with `label: "event-click"`
  - `comment-save-link-node` with `label: "clipboard"`
  - `comment-write-link-node` with `label: "command"`
  - `comment-send-js-node` reduced to no-op when main path uses `Presskey Enter`
- Layout pattern from latest wrap:
  - Keep `MAIN PATH` and `FALLBACK PATH` on separate rows in editor when workflow starts accumulating recovery logic.
  - Update note blocks so the visual graph explains the real path, not stale behavior.

## Verified Workflow Pattern: file input to string input migration
Observed from `[TikTok] Like comment share - No Text File` in `db.db`.

- Final trigger parameters used:
  - `link_url`
  - `comment_text`
  - `comment_link_file`
- Safe migration rules:
  - convert input params in both trigger parameter arrays
  - keep output file params like `comment_link_file` as `filepath`
  - replace old `read-file-text` input nodes with `javascript-code` loaders that populate same downstream variables
- Concrete loader pattern used:
  - `read-comment-node` sets `comment_line` from `{{variables.comment_text}}`
  - `read-links-node` sets `raw_links` from `{{variables.link_url}}`
  - `read-links-node` also sets guard variable like `link_input_consumed`
  - on next pass, loader returns empty `raw_links` so existing parser/router reaches `eof`
- Loop migration warning:
  - old list-processing graphs often route `skip` or `next` back into `read-links-node`
  - after moving to single string input, that branch usually must end workflow or feed one-shot loader behavior
  - otherwise same URL can loop forever
- Why this pattern is useful:
  - keeps downstream parser, router, and open-url nodes mostly unchanged
  - minimizes graph surgery while removing dependency on external text files

## Verified Workflow Pattern: TikTok upload trigger params
Observed from `[TikTok] Upload Video` in `db.db`.

- Trigger parameters used:
  - `video_file`
  - `caption_file`
  - `hashtag_file`
  - `video_link_file`
- GemLogin stores manual trigger inputs in 2 places:
  - `workflow_dict["trigger"]["parameters"]`
  - trigger node `data.parameters`
- If only top-level trigger params are updated, DB may look correct while GemLogin editor or MCP tool output still misses the new field.
- Safe patch rule:
  - update both parameter arrays in same write
  - then reload UI
  - then verify through DB readback or MCP script listing

## Verified Workflow Pattern: TikTok upload post confirmation
Observed from `[TikTok] Upload Video` plus live TikTok Studio runtime.

- Main publish path is not always one click:
  - `Post`
  - wait
  - detect modal
  - conditional `Post now`
- Real modal text seen in runtime:
  - `Continue to post?`
  - button `Post now`
- Reason:
  - TikTok can keep content checks running after first post click, then ask for confirmation before final publish.
- Stable workflow pattern:
  - JS node sets `post_confirm_state` to `confirm` or `done`
  - `conditions` block routes:
    - `confirm` -> click `Post now`
    - `done` -> continue without extra click
- Avoid blind double-click posting. Detection plus branch is safer and easier to debug.

## Verified Workflow Pattern: latest uploaded video link capture
Observed from `[TikTok] Upload Video` plus live TikTok Studio content page.

- Stable capture path after posting:
  - open `https://www.tiktok.com/tiktokstudio/content`
  - wait for content list
  - JS reads first `a[href*="/video/"]`
  - store URL in variable such as `latest_video_url`
  - route on `latest_video_state`
  - append into user-chosen output file with `file-action`
- Why this path is preferred:
  - content page already orders posts by `Created on`
  - first `/video/` anchor is simple to verify in runtime
  - avoids scraping transient upload dialogs
- Built-in write pattern:
  - `file-action`
  - `writeMode: "append"`
  - `appendMode: "newLine"`
  - `filePath: "{{variables.video_link_file}}"`
  - `inputData: "{{variables.latest_video_url}}"`

## Verified Workflow Pattern: warm feed loop routing
Observed from `[TikTok] Warm-up Feed` in `db.db`.

- Stable return path:
  - every action branch converges into `scroll-node -> scroll-pause-node -> scroll-loop-node`
- Reason:
  - like/comment/share/repost each have local failure modes
  - loop control becomes much easier when only one path owns next-video transition
- Real breakages seen during debugging:
  - action branch ended on custom mini-loop instead of shared scroll chain
  - loop breakpoint looked valid by `type` but used wrong `label` and stale trigger-shaped `data`
  - conditions branch matched state but `sourceHandle` did not match condition id, so runtime returned `nextBlockId = null`
- Maintenance rule:
  - after loop surgery, read back both node positions and edge handles, not only node code

## Editing Guidance From Verified Workflow
- When user asks what a `conditions` block does:
  - do not read the block alone
  - find upstream variable-setting node first
  - map each branch to its outgoing `sourceHandle`
  - then explain downstream targets
- When user asks for "copy link from UI and save to text file", do not jump to JS first.
- First check whether workflow can be modeled as:
  - click block
  - clipboard get block
  - command/file-action append block
- If writing to text file:
  - `file-action` is good for direct append of known variable.
  - `command` is good when user explicitly wants shell or PowerShell behavior.
- When adding new workflow inputs:
  - patch both top-level trigger params and `trigger-node.data.parameters`
  - reload UI
  - verify new field through MCP or editor readback instead of trusting DB only
- When replacing file inputs with string params:
  - keep downstream variable names stable where possible
  - replace `read-file-text` node with one-shot JS loader if graph expects a reader node
  - inspect loop-back edges and skip branches before trusting old router behavior
  - preserve output file params if user still wants append-to-file behavior
- When changing submit logic:
  - trace every incoming and outgoing edge on the affected path
  - remove duplicate submit side effects, not just duplicate selectors
- When publish flow can show a confirmation modal:
  - model it as `wait -> detect -> route -> click confirm`
  - keep confirm branch and no-confirm branch explicit in graph
- When saving latest uploaded content URL:
  - prefer opening content list and reading first `/video/` anchor
  - prefer `file-action` append over `command` when only writing one resolved variable
- When patching path order, update both:
  - node positions for readability in editor
  - edges in `drawflow.edges`
- When a conditions branch appears to route correctly in editor but stops at runtime:
  - compare `data.conditions[*].id`
  - compare outgoing edge `sourceHandle`
  - fix handle mismatch before blaming selectors or JS
- When cleaning up loop-heavy workflows:
  - make shared return path explicit
  - keep `scroll`, `pause`, and `loop-breakpoint` adjacent in layout
  - use note blocks to separate `SETUP`, action groups, and `END`
- After flow becomes stable, add short edge labels:
  - outcome-based
  - readable at zoomed-out editor level
  - consistent across main path and fallback path
- If workflow uses note blocks, update note text so editor reflects new main path and fallback path.

## Verified Lessons From Latest Wrap
Source: `D:\Littar-Codex\Kvasir\memory\retrospectives\2026-06\05\09.45_gemlogin_tiktok_workflow_stabilization.md`

- Read the whole graph before patching:
  - inspect node data
  - inspect edge routing
  - do not assume UI symptom is only a selector issue
- Prefer single-responsibility nodes:
  - if `press-key Enter` is the submit path, JS submit block should not also submit
  - fallback blocks should not keep touching the same side effect as the main path unless explicitly intended
- Treat layout as debugging infrastructure:
  - separate main row and fallback row early
  - keep note blocks accurate after logic changes
- Treat labeled edges as debugging infrastructure:
  - conditions blocks become faster to explain when branch edges are labeled
  - fallback-heavy graphs become readable without opening every node
- Treat trigger inputs as dual-source metadata:
  - missing one copy can create false confidence from DB inspection alone
  - verify parameter visibility from actual workflow listing after reload
- DB-first editing is fast, but only safe with:
  - timestamped backup before every write
  - reload immediately after every write

## Trigger
Use when user asks to:
- "Edit workflow X in db"
- "Batch update GemLogin workflows"
- "Hack workflow logic directly"
- "Change start URL for all workflows"
- "Delete workflow X in GemLogin"

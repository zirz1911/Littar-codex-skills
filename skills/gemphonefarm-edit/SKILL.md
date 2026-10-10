---
name: gemphonefarm-edit
description: Directly read, patch, build, and install GemPhoneFarm workflow JSON files — either on-disk .GemPhoneFarm files or via the :1256 local API. Use when user asks to edit, create, rename, batch update, or debug GemPhoneFarm automation workflows.
---

# gemphonefarm-edit Skill

Directly manipulate GemPhoneFarm automation workflows — read `.GemPhoneFarm` JSON files, patch drawflow node graphs, build workflows from specs, install via API, and debug runtime behavior.

## Source Material

This skill was built from:
- **Learn output**: 94 production `.GemPhoneFarm` workflow files analyzed across 6 team members (Boss, Jed, Jacob, Paji, Boom, PAT) — see `Kvasir/learn/local/gemphonefarm-scripts/`
- **Wrap context**: GemPhoneFarm MCP server build, IPC discovery, state-first XPath debugging sessions
- **Template**: `gemlogin-edit` skill (shared DB-first editing philosophy, adapted for GemPhoneFarm's drawflow format and API)

## Paths

### Workflow files (on-disk)
- Source collection: `/Users/pajipan/Downloads/Gemphonefarm/` (94 `.GemPhoneFarm` files across 6 team-member folders)
- Individual workflow files follow naming: `Workflow Name.GemPhoneFarm` (single `.GemPhoneFarm` extension) or `Workflow Name.GemPhoneFarm.GemPhoneFarm` (double extension from export bug)

### API (local)
- Base URL: `http://127.0.0.1:1256`
- Script list: `GET /scripts` — list all installed scripts
- Script create/update: `POST /scripts` — create new (wrap workflow in `script` field); overwrite by deleting first with `DELETE /api/scripts/{id}`
- Script delete: `DELETE /api/scripts/{id}`
- Script detail: `GET /scripts/{id}` returns 404 — use `GET /scripts` and filter by name/id instead
- Execute: `POST /api/scripts/execute/:id`
- Device interaction: **IPC broken** — use ADB directly (see Rules)

> **Path asymmetry note**: `POST /scripts` uses NO `/api/` prefix, while `DELETE /api/scripts/{id}` DOES use `/api/`. This matches the GemPhoneFarm Express server's actual route registration.

### Database (GemPhoneFarm internal, read-only from skill perspective)
- Path: `~/.GemPhoneFarm/app/db.db` (SQLite, platform-dependent)
- Table: `apps` — contains installed workflow JSON in `script` column
- **Prefer API over DB write** — API `POST /scripts` is cross-platform reliable; DB path uses `process.env.pathRoot + "\\db.db"` which creates literal `\db.db` on macOS

## Capability

- Read any `.GemPhoneFarm` workflow JSON from disk
- Inspect drawflow node graph (nodes, edges, positions, viewport)
- Patch workflow logic — change selectors, delays, conditions, edge routing
- Build workflows from clean specs (via `gemphonefarm_build_workflow` MCP tool)
- Install workflows via API `POST /scripts` (with DELETE-before-CREATE for updates)
- Rename, delete workflows
- Validate JSON structure before install
- Debug runtime issues: state-first XPath matching, fallback edge routing, loop breakpoints

## Scripts

- `scripts/reload_gemphonefarm.py` — Cross-platform reload helper. Tries CDP on `localhost:9222-8315` first, then AppleScript `Cmd+R` on macOS, then PowerShell `Ctrl+R` on Windows.
- Bundled with this skill. Called automatically after every `build_and_install_workflow` MCP call or API write.

## Rules

### 1. Always Backup
Before modifying any `.GemPhoneFarm` file, copy it with a timestamp suffix:
```bash
cp "file.GemPhoneFarm" "file.GemPhoneFarm.bk.$(date +%Y%m%d_%H%M%S)"
```

### 2. JSON Integrity
Validate JSON structure before and after every edit. The top-level schema is:
```json
{
  "extVersion": "1.0.0" | 2,
  "name": "string",
  "drawflow": { "nodes": [...], "edges": [...], "position": [x,y], "zoom": float, "viewport": {...} },
  "settings": { "saveLog": true, "debugMode": false, "restartTimes": 3, "onError": "stop-workflow", ... },
  "trigger": { ... },
  "author": "string"
}
```

### 3. Mandatory Reload UI After Every API Write
After installing, updating, or deleting a workflow via `POST /scripts` or `DELETE /api/scripts/:id`, reload the GemPhoneFarm UI so the scripts list refreshes immediately. The API writes to the database but the Electron renderer does not auto-refresh.

Use the bundled reload script: `scripts/reload_gemphonefarm.py`

```bash
python3 scripts/reload_gemphonefarm.py
```

The script tries CDP first (Electron remote debugging on ports 9222-8315), then falls back to AppleScript `Cmd+R` on macOS. If both fail, tell the user to press `Cmd+R` (macOS) or `Ctrl+R` (Windows) in the GemPhoneFarm window.

**After every `build_and_install_workflow` MCP call, run the reload script automatically.**

### 3.1 Throwaway Python Must Be Temporary
Prefer inline `python - <<'PY'` for one-off workflow inspection, file patching, or API checks. If a `.py` file is unavoidable, create it in temp or `scratch/` and delete it immediately after execution. Do not leave `temp_*.py`, `patch_*.py`, or `fix_*.py` in shared paths.

### 4. Nodes Can Be Array or Object
- **extVersion "1.0.0"**: `drawflow.nodes` is a JSON **array** `[{...}, {...}]`
- **extVersion 2**: `drawflow.nodes` is a JSON **object** keyed by node ID `{"id1": {...}, "id2": {...}}`
- When patching on-disk files, preserve the format. Do not mix array and object styles.
- **API install format EXCEPTION**: `POST /scripts` requires `drawflow.nodes` as array `[{...}]` regardless of extVersion. Dict-format nodes cause empty blocks in UI. Convert dict→array before API install: `list(nodes.values())`.

### 5. State-First XPath — THE CRITICAL RULE
Derive XPath selectors from the **current live UI state** of the screen the block will run against. Never reuse old XPath from stale dumps.

**Failure mode**: Using XPath from a previous screen state causes false fixes:
- Comment input state changes after typing
- Send button `resource-id` or `content-desc` changes between states
- Close button label differs between drawers, popups, or app versions

**Before editing any touch/type-text/find-text block**:
1. Put the phone on the exact screen state the block should target
2. Dump UI hierarchy from that exact state (`gemphonefarm_dump_ui_hierarchy`)
3. Extract selector from that state only
4. If a later block runs after a state transition, dump again after the transition
5. Do not reuse old XPath just because it worked in a previous dump

### 6. Read Whole Graph Before Patching
Inspect both node data AND edge routing before changing behavior. Do not assume symptoms are only selector problems. Trace:
- `drawflow.nodes` — all block definitions
- `drawflow.edges` — all connections, including fallback edges (styled `stroke: #ff6b6b`)

### 7. Block Type vs Label
Many executable nodes have generic `type: "BlockBasicWithFallback"`. The real block behavior is in `label`. Key labels and their count across 94 workflows:

| Label | Count | Purpose |
|-------|-------|---------|
| `touch` | 1057 | Tap at XPath/coordinate |
| `delay` | 340 | Time delay |
| `conditions` | 268 | Branching logic |
| `image-search` | 219 | Image-based element detection |
| `type-text` | 170 | Type text into field |
| `ADB-shell-command` | 109 | Raw ADB shell |
| `insert-data` | 102 | Read from CSV/data table |
| `start-app` | 100 | Launch app by package |
| `find-text` | 97 | Text-based element detection |
| `repeat-task` | 93 | Loop N times |
| `element-exists` | 85 | Check element in view |
| `swipe-scroll` | 84 | Scroll/swipe gesture |
| `stop-app` | 84 | Force-stop app |
| `loop-breakpoint` | 76 | Loop exit |
| `press-back` | 71 | Android back button |
| `random` | 63 | Random number generator |
| `read-file-text` | 62 | Read from text file |
| `find-text-OCR` | 57 | OCR text detection |
| `loop-data` | 50 | Iterate CSV rows |
| `press-key-phone` | 47 | Key press |
| `regex-variable` | 43 | Regex extraction |
| `command` | 42 | Shell command |
| `javascript-code` | 38 | JS in WebView |
| `close-all-app` | 30 | Kill all apps |
| `gem-ai` | 13 | Gemini AI call |
| `webhook` | 12 | HTTP webhook |

### 8. The Fallback Pattern Is Implicit Try/Catch
`BlockBasicWithFallback` nodes have two output ports:
- **`{id}-output-1`** (green): success — element found, action completed
- **`{id}-output-fallback`** (red, styled `stroke: #ff6b6b`): failure — element not found, timeout

This is GemPhoneFarm's built-in error handling. Common patterns:
1. **Retry loop**: `fallback` → back to same node
2. **Alternative path**: `fallback` → different UI interaction (scroll then retry)
3. **Error terminal**: `fallback` → `stop-app` or `end`

### 9. Delay Units — Seconds vs Milliseconds (VERIFIED FROM PRODUCTION)

⚠️ **Critical — wrong units silently break timing.**

| Delay Type | Field | Unit | Example | Source |
|-----------|-------|------|---------|--------|
| Action block delay | `data.delay` | **SECONDS** | `"2,4"` = 2-4s | Production: `touch delay=2,4`, `press-back delay=4` |
| BlockDelay node | `data.time` | **MILLISECONDS** | `"3000,5000"` = 3-5s | Production: `BlockDelay time=2000`, `time=3000,5000` |
| Global block delay | `settings.blockDelay` | **SECONDS** | `0` | Settings |

**Proof from production workflows:**
```
touch  LIKE:     data.delay = "2,4"     ← 2-4 SECONDS
touch  FAV:      data.delay = "2,4"     ← 2-4 SECONDS  
touch  COMMENT:  data.delay = "4,5"     ← 4-5 SECONDS
type-text:       data.delay = "3,5"     ← 3-5 SECONDS
swipe-scroll:    data.delay = "5,8"     ← 5-8 SECONDS
press-back:      data.delay = "4"       ← 4 SECONDS
BlockDelay:      data.time  = "2000"    ← 2000 MILLISECONDS = 2s
BlockDelay:      data.time  = "3000,5000" ← 3-5s (random)
```

**Rules:**
- NEVER put millisecond values (≥100) in action block `data.delay`. If you see `delay: 500` or `delay: 3000` on a touch/type-text/etc node, it's wrong.
- BlockDelay uses field `time` (NOT `delay`). Values are in milliseconds.
- Default delays for feed automation: touch 1-3s, type-text 1-2s, press-key 1s, press-back 1s, swipe 2-4s, start-app 3-5s.

### 10. API DELETE-Before-CREATE for Updates
`POST /scripts` does **not overwrite** existing scripts. To update:
1. `DELETE /api/scripts/{id}` — remove old version
2. `POST /scripts` — create new version
3. The MCP `gemphonefarm_build_and_install_workflow` handles this automatically (API-first, DB fallback). The `gemphonefarm_install_workflow` MCP tool also uses API-first since the fix.

### 11. IPC Is Broken — Use ADB Directly
GemPhoneFarm's Express server at `:1256` cannot execute device interactions because `main.js:980` calls `startServer()` without passing `mainWindow`. All IPC endpoints fail with `"Cannot read properties of undefined (reading 'webContents')"`.

| Broken API | ADB Replacement |
|------------|----------------|
| `POST /api/devices/start/:id` | `adb shell monkey -p PKG 1` |
| `POST /api/devices/close/:id` | `adb shell am force-stop PKG` |
| `POST /tap` | `adb shell input tap X Y` |
| `POST /swipe` | `adb shell input swipe X1 Y1 X2 Y2 DUR` |
| `POST /pressKey` | `adb shell input keyevent KEYCODE` |
| Screenshot | `curl http://127.0.0.1:PORT/screenshot/0` (atx-agent) |

**Working API endpoints** (DB-backed, no IPC needed):
- Device list: `GET /api/devices`
- Group CRUD: `GET/POST/PUT/DELETE /api/groups`
- Script list: `GET /scripts`, create: `POST /scripts`, delete: `DELETE /api/scripts/{id}`
- Profile detail: `GET /api/profiles/:id`

> **Path asymmetry**: `POST /scripts` uses NO `/api/` prefix; `DELETE /api/scripts/{id}` DOES use `/api/`. This matches GemPhoneFarm's Express route registration.

### 12. Conditions Need Upstream Context
Do not explain or patch a `conditions` block in isolation. First find which earlier node sets the variable that drives the branch. Map:
- Upstream variable-setting node → variable name
- Condition definitions in `data.conditions[]` → condition IDs
- Outgoing edges by `sourceHandle` → `{nodeId}-output-{conditionId}`
- Downstream target nodes

### 13. Condition Branches — Use Fallback for Else

Every branch MUST have `conditions` array — `"conditions": []` is OK, missing/undefined throws `TypeError: e is not iterable`.

**Recommended: single branch + fallback** (not dual branches with empty skip):
- Branch met → edge `{nodeId}-output-{conditionId}`
- Branch NOT met → edge `{nodeId}-output-fallback`

Production `[TIKTOK] - Post Interactions` uses this single-branch pattern.

### 14. Condition Handles Must Match Condition IDs
If a conditions branch visually exists but runtime shows `nextBlockId = null`, inspect each outgoing edge `sourceHandle`. It must match the exact condition id pattern like `{nodeId}-output-{conditionId}`. Handle mismatch is the most common silent failure.

### 15. Repeat-Task Loop Pattern (NO loop-breakpoint needed)

The standard loop uses `repeat-task` with 2 outputs. **Do NOT add `loop-breakpoint` for normal loop termination.**

```
repeat-task output-2 → watch-delay (each iteration: go to loop body)
  ... loop body (watch → like → comment → save → share → swipe) ...
  swipe → repeat-task input-1 (iteration complete, come back)
repeat-task output-1 → end (all iterations done, exit loop)
```

⚠️ `output-2` = keep looping, `output-1` = loop complete. Production workflow `[TIKTOK] - Post Interactions` uses exactly this pattern with no loop-breakpoint.

### 16. Loop Breakpoint (for EARLY exit only)

`loop-breakpoint` is for breaking out of a loop BEFORE `repeatFor` count is exhausted (conditional early exit). For normal loop termination, `repeat-task output-1` handles completion naturally.

A valid loop breakpoint needs:
- `type: "BlockLoopBreakpoint"`
- `label: "loop-breakpoint"`
- `data.loopId` — unique ID, production uses short strings like `"wF0iD-"`, `"MainLoop"`, `"main"`
- `data.clearLoop: false`

### 17. One Return Path Per Loop
Route all action branches back into one shared `swipe → repeat-task input-1` chain unless behavior truly differs. Separate mini-loops are hard to debug.

### 18. Trigger Params Need Dual Sync (extVersion 2 only)
In extVersion 2 workflows, trigger parameters exist in two places:
- `workflow.trigger.parameters` (top-level)
- Trigger node `data.parameters` (inside drawflow)

Both must be updated together. Missing one side can leave UI or MCP discovery out of sync.

### 19. Touch Uses `xPath`, Type-Text Uses `selector`
Critical schema difference verified from production workflows:
- **`touch`** block: XPath in `data.xPath` — array of `[{id, value}]` with `selectBy: "selector"`
- **`type-text`** block: input field selector in `data.selector`, text content in `data.inputText` or `data.textValue`
- **`press-key-phone`** block: key code in `data.keyCode`
- **`find-text-OCR`** block: search text in `data.textSearch`, result in `data.textFound`

### 20. Prefer Built-in Blocks Over Custom JS
If user intent can be expressed with existing block types, use them. Only use `javascript-code` when built-in blocks cannot express the behavior cleanly. The production workflows overwhelmingly use built-in blocks — only 38 `javascript-code` instances across 94 workflows.

### 21. Layout Is Part of Maintenance
When fallback logic grows, keep `MAIN PATH` and `FALLBACK PATH` visually separated in editor and update note blocks after logic changes.

---

## Block Type Reference

Every node MUST use the correct `type` matching its `label`. Using wrong types (e.g. `BlockBasicWithFallback` for `delay`) silently breaks behavior.

| Label | Correct `type` | Notes |
|-------|---------------|-------|
| `trigger` | `BlockBasic` | Entry point, single output `output-1` |
| `end` | `BlockBasic` | Terminal, no outputs |
| `delay` | `BlockDelay` | Time delay, single output |
| `conditions` | `BlockConditions` | Multi-branch, outputs named `output-{conditionId}` |
| `repeat-task` | `BlockRepeatTask` | Two outputs: `output-1` (done), `output-2` (loop) |
| `loop-breakpoint` | `BlockLoopBreakpoint` | Loop exit, two outputs |
| `note` | `BlockNote` | Visual annotation, no outputs |
| `blocks-group` | `BlockGroup` | Visual grouping |
| **Everything else** | `BlockBasicWithFallback` | touch, start-app, type-text, random, swipe-scroll, press-back, press-key-phone, javascript-code, ADB-shell-command, find-text, find-text-OCR, image-search, element-exists, read-file-text, etc. |

### Edge Handle Format (CRITICAL)

Edges MUST use exact handle strings. Wrong handles = broken connections.

```
Regular node output:  {nodeId}-output-1
Fallback output:      {nodeId}-output-fallback
Condition output:     {nodeId}-output-{conditionId}     ← matches data.conditions[].id
Repeat-task loop:     {nodeId}-output-2
All inputs:           {targetId}-input-1
```

⚠️ **Do NOT double the `output-` prefix**. `output-output-1` is WRONG. Correct is `output-1`.

### API Install Format

```json
{
  "id": "workflow-unique-id",
  "name": "Display Name",
  "description": "...",
  "version": "1.0.0",
  "script": {
    "extVersion": 2,
    "name": "Display Name",
    "description": "...",
    "drawflow": {
      "nodes": [
        {"id": "n1", "type": "BlockBasic", "label": "trigger", "data": {...}, "position": {...}, "initialized": false},
        {"id": "n2", "type": "BlockBasic", "label": "end", "data": {...}, "position": {...}, "initialized": false}
      ],
      "edges": [
        {"id": "vueflow__edge-...", "source": "n1", "target": "n2", "sourceHandle": "n1-output-1", "targetHandle": "n2-input-1"}
      ],
      "position": [300, 100],
      "zoom": 1.0,
      "viewport": {}
    },
    "settings": {
      "publicId": "", "blockDelay": 0, "saveLog": true, "debugMode": false,
      "restartTimes": 3, "notification": true, "execContext": "popup",
      "reuseLastState": false, "inputAutocomplete": true,
      "onError": "stop-workflow"
    },
    "trigger": {
      "type": "manual",
      "parameters": [
        {"name": "myParam", "label": "My Param", "type": "number", "defaultValue": "10", "id": "p1"}
      ]
    },
    "author": "Codex"
  }
}
```

> **CRITICAL**: `drawflow.nodes` MUST be a JSON **array** `[{...}]` for API install, regardless of extVersion. Dict-format nodes stored in on-disk `.GemPhoneFarm` files must be converted to array before `POST /scripts`. Dict nodes cause empty blocks in UI.

- `POST /scripts` — create (wrap workflow in `script` field)
- `DELETE /api/scripts/{id}` — remove before re-create to allow updates
- After install, run `scripts/reload_gemphonefarm.py` to refresh UI

### When `build_and_install_workflow` Produces Wrong Output

The `build_workflow` MCP tool may produce incorrect:
- Block types (all `BlockBasicWithFallback`)
- Edge handles (doubled `output-output-` prefix)
- Missing `description`/`version` fields

**Fix**: Craft the workflow JSON directly using correct types and handles from this reference. Install via `POST /scripts` or the `gemphonefarm_build_and_install_workflow` MCP tool (API-first, DB fallback). The `gemphonefarm_install_workflow` MCP tool also uses API-first since the fix — it no longer requires manual UI restart.

---

## Verified Block Schemas

### Trigger Block (BlockBasic, label: "trigger")
```json
{
  "type": "BlockBasic",
  "label": "trigger",
  "data": {
    "type": "manual",
    "interval": 60,
    "delay": 0,
    "url": "",
    "parameters": [
      {
        "name": "urlPost",
        "label": "Post's URL",
        "type": "string",
        "defaultValue": "",
        "placeholder": "https://vt.tiktok.com/...",
        "id": "_q6X"
      }
    ]
  }
}
```
Parameter types: `string`, `number`, `checkbox`, `filepath`.

### Touch Block (BlockBasicWithFallback, label: "touch")
```json
{
  "type": "BlockBasicWithFallback",
  "label": "touch",
  "data": {
    "selectBy": "selector",
    "xPath": [
      {"id": "xpath-touch-target-1", "value": "//node[@resource-id='com.ss.android.ugc.trill:id/btn_like']"}
    ],
    "x": "", "y": "",
    "waitForSelector": true,
    "waitSelectorTimeout": 15000,
    "multiple": false,
    "delay": 500
  }
}
```
XPath selectors use `//node[@resource-id='...']` or `//node[@content-desc='...']` format matching Android UI hierarchy XML output.

### Type-Text Block (BlockBasicWithFallback, label: "type-text")
```json
{
  "type": "BlockBasicWithFallback",
  "label": "type-text",
  "data": {
    "selector": "//node[@resource-id='com.ss.android.ugc.trill:id/et_comment']",
    "inputText": "{{variables.comment_text}}",
    "selectBy": "selector",
    "clearBefore": true,
    "delay": 300
  }
}
```
Note: field name varies — some workflows use `inputText`, others `textValue`. Check both when reading existing workflows.

### Start-App Block (BlockBasicWithFallback, label: "start-app")
```json
{
  "type": "BlockBasicWithFallback",
  "label": "start-app",
  "data": {
    "icon": "riPlayLine",
    "disableBlock": false,
    "packageName": "com.ss.android.ugc.trill",
    "description": "เปิด TikTok",
    "delay": "3,5"
  }
}
```
Field is `packageName` (NOT `appPackage`). Delay in seconds (matching other action blocks).

### Conditions Block (BlockConditions, label: "conditions")
```json
{
  "type": "BlockConditions",
  "label": "conditions",
  "data": {
    "icon": "riAB",
    "disableBlock": false,
    "description": "",
    "conditions": [
      {
        "id": "DbZnqEnItE-fL6FSkDQG-",
        "name": "LIKE",
        "conditions": [
          {
            "id": "db5m3wv1L0fLCYznaq9pD",
            "conditions": [
              {
                "id": "c8rRqtfmDEdOdApImwpTK",
                "items": [
                  {"type": "value", "category": "value", "data": {"value": "{{variables.randLike}}"}, "id": "r1Z0dEScjTOEZVNlHoue2"},
                  {"category": "compare", "type": "lte", "id": "kfzsCm0U1g6nAQFafZl65"},
                  {"type": "value", "category": "value", "data": {"value": "{{variables.likeRate}}"}, "id": "bTT54VBA5nMeRRfe_rtwr"}
                ]
              }
            ]
          }
        ]
      }
    ],
    "retryConditions": false,
    "retryCount": 10,
    "retryTimeout": 1000
  }
}
```
⚠️ **Every level needs unique `id`**: condition branches, nested groups, and every item in `items[]`. IDs are long random strings (~21 chars, alphanumeric + `-_`). Edge handles use these IDs: `{nodeId}-output-{conditionId}`.

**Compare types observed in production:**
| Type | Meaning |
|------|---------|
| `eq` | Equal |
| `lte` | Less than or equal |
| `itr` | Is truthy (for checkboxes) |
| `element#exists` | Element found on screen |
| `element#notExists` | Element NOT found |

Read conditions in 4 parts: upstream variable node → branch definitions → outgoing edge handles → downstream targets.

### Delay Block (BlockDelay, label: "delay")
```json
{
  "type": "BlockDelay",
  "label": "delay",
  "data": {
    "icon": "riTimerLine",
    "disableBlock": false,
    "description": "",
    "time": "3000,5000"
  }
}
```
Field is `time` (NOT `delay`). Value in **milliseconds**. Fixed: `"3000"`, range: `"3000,5000"`. Can reference variables: `"{{variables.watchTime}}"`. Action block `data.delay` is in **seconds** — see Rule #9.

### Random Block (BlockBasicWithFallback, label: "random")
```json
{
  "type": "BlockBasicWithFallback",
  "label": "random",
  "data": {
    "icon": "riDiceLine",
    "disableBlock": false,
    "description": "",
    "language": "EN",
    "type": "number",
    "categories": "simple",
    "command": "",
    "variableName": "randLike",
    "delay": 0,
    "fromNumber": "0",
    "toNumber": "100"
  }
}
```
Fields are `fromNumber` and `toNumber` (strings, NOT `min`/`max`). Values always strings: `"0"`, `"100"`, `"{{variables.gglen}}"`. Result stored in `{{variables.<variableName>}}`. Advanced mode uses `categories: "advanced"` + `command` with JavaScript.

### Repeat-Task Block (BlockRepeatTask, label: "repeat-task")
```json
{
  "type": "BlockRepeatTask",
  "label": "repeat-task",
  "data": {
    "repeatFor": "{{variables.numScrolltoNext}}"
  }
}
```
Two outputs: `output-1` (completed, continues to next step) and `output-2` (repeat, loops back).

### ADB Shell Command Block (BlockBasicWithFallback, label: "ADB-shell-command")
```json
{
  "type": "BlockBasicWithFallback",
  "label": "ADB-shell-command",
  "data": {
    "command": "am start -a android.intent.action.VIEW -d {{variables.urlPost}}",
    "assignVariable": false,
    "variableName": "",
    "delay": 1000
  }
}
```

### JavaScript-Code Block (BlockBasicWithFallback, label: "javascript-code")
```json
{
  "type": "BlockBasicWithFallback",
  "label": "javascript-code",
  "data": {
    "icon": "riCodeSSlashLine",
    "disableBlock": false,
    "description": "คำนวณเวลา",
    "timeout": 20000,
    "context": "website",
    "code": "return (Date.now() - {{variables.startTime}}) / 60000;",
    "preloadScripts": [],
    "everyNewTab": false,
    "runBeforeLoad": false,
    "assignVariable": true,
    "variableName": "elapsedMinutes",
    "delay": "0"
  }
}
```
⚠️ Required fields often missed: `timeout` (number), `context` ("website"), `preloadScripts` (array, can be `[]`), `everyNewTab` (false), `runBeforeLoad` (false). Missing `preloadScripts` causes `TypeError: Cannot read properties of undefined (reading 'map')`.

Use `return <value>` + `assignVariable: true` + `variableName` to store result. Template variables `{{variables.xxx}}` are resolved before JS execution.

### Find-Text OCR Block (BlockBasicWithFallback, label: "find-text-OCR")
```json
{
  "type": "BlockBasicWithFallback",
  "label": "find-text-OCR",
  "data": {
    "findType": "screenshot",
    "textSearch": "Chrome",
    "textFound": "",
    "isTouchText": true,
    "assignVariable": false,
    "variableName": "",
    "crop": false,
    "startX": 0, "startY": 0, "endX": 100, "endY": 100
  }
}
```

### End Block (BlockBasic, label: "end")
```json
{
  "type": "BlockBasic",
  "label": "end",
  "data": {
    "icon": "riStopLine",
    "disableBlock": false,
    "description": ""
  }
}
```

### Note Block (BlockNote, label: "note")
```json
{
  "type": "BlockNote",
  "label": "note",
  "data": {
    "icon": "riFileEditLine",
    "disableBlock": false,
    "note": "SECTION TITLE\nDescription of what follows",
    "drawing": false,
    "width": 960, "height": 110,
    "color": "green",
    "fontSize": "large"
  }
}
```
Use for: section headers, operator guidance, separating main flow from recovery flow.

### Edge Structure
```json
{
  "id": "vueflow__edge-{sourceId}{sourceId}-output-1-{targetId}{targetId}-input-1",
  "type": "bezier",
  "source": "node-id", "target": "node-id",
  "sourceHandle": "{id}-output-1",
  "targetHandle": "{id}-input-1",
  "markerEnd": "arrowclosed",
  "style": "stroke: #ff6b6b"
}
```
- **Success edges**: `sourceHandle: "{id}-output-1"`, no special style
- **Fallback edges**: `sourceHandle: "{id}-output-fallback"`, styled `stroke: #ff6b6b` (red)
- **Condition edges**: `sourceHandle: "{id}-output-{conditionId}"`
- **Custom type**: used for trigger → first action connections instead of `bezier`

---

## Verified Workflow Patterns

### Archetypal Workflow Structure
```
trigger
  → start-app
  → touch / find-text / element-exists (navigate to target UI)
  → type-text (fill input)
  → touch (submit)
  → conditions (check success/failure)
     → success: repeat-task or end
     → failure: delay → loop-back or end
  → stop-app / close-all-app (cleanup)
  → end
```

### Anti-Detection / Humanization
- **Random delays**: `random` node generates number → used in delay time as `{{variables.Random}}`
- **Randomized XPath indexing**: `(//node[@content-desc="Add friend"])[{{variables.Randomfriend}}]` — avoids deterministic click patterns
- **Scroll between touches**: `swipe-scroll` nodes inserted between interaction steps
- **Unicode zero-width chars**: Some workflows use invisible Unicode chars in selector text — anti-OCR technique

### Variable System
Syntax: `{{variables.VARNAME}}` (Handlebars-style). Sources:
- Trigger `parameters` array
- `random` node output
- `insert-data` node (CSV row values)
- `regex-variable` node (extractions)
- `get-attribute` node (UI element attributes)
- `javascript-code` node (custom JS output)

Resource references: `{{resource.PlatformName.FieldName}}` for saved credentials (e.g., `{{resource.Facebook.Username}}`).

### Login Flow Pattern (Jacob's State Machine)
```
start-app
  → element-exists (check if login needed)
     → output-1 (already logged in): skip to main flow
     → output-fallback (login needed): enter credentials
  → type-text (username)
  → type-text (password)
  → touch (login button)
  → element-exists (wait for main UI)
  → conditions (verify success)
     → success: proceed
     → failure: retry loop back to start-app
```

### TikTok Interaction Pipeline
```
trigger(urlPost, watchTime, numScrolltoNext, toLIKE, toFAV, toCOMMENT)
  → ADB-shell-command (open URL via intent)
  → element-exists (wait for video player)
  → delay ({{variables.watchTime}})
  → conditions (check toLIKE)
     → true: touch (like button)
     → false: skip
  → conditions (check toCOMMENT)
     → true: touch (comment field) → type-text → press-key-phone (Enter)
     → false: skip
  → swipe-scroll (next video)
  → repeat-task (back to delay, {{variables.numScrolltoNext}} times)
  → end
```

### Cross-Platform Posting Pattern (Jacob's Mega-Poster)
```
trigger(videoFile, caption)
  → start-app (Facebook) → post → stop-app
  → start-app (Instagram) → post → stop-app
  → start-app (X/Twitter) → post → stop-app
  → start-app (YouTube) → post → stop-app
  → start-app (Line Voom) → post → stop-app
  → start-app (Lemon8) → post → stop-app
  → end
```

### Line-State Router Pattern
```
parse-node (JS) → sets line_state: "valid" | "skip" | "eof"
  → conditions (route on {{variables.line_state}})
     → valid: open URL → interact → loop back to read-next
     → skip: loop back to read-next
     → eof: end
```
Observed in TikTok Like comment share workflows. Edge labels (`Open URL`, `Skip line`, `No more link`) make the graph readable without opening every node.
```

---

## Automation Script Template

Use Python to interact with `.GemPhoneFarm` files and the local API:

```python
import json, os, shutil, sys, requests
from datetime import datetime
from pathlib import Path

API_BASE = "http://127.0.0.1:1256"
SOURCE_DIR = "/Users/pajipan/Downloads/Gemphonefarm"

def backup_file(filepath):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = f"{filepath}.bk.{ts}"
    shutil.copy2(filepath, backup)
    print(f"[backup] {backup}")
    return backup

def read_workflow_file(filepath):
    """Read a .GemPhoneFarm JSON file from disk."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def write_workflow_file(filepath, workflow_dict):
    """Write workflow JSON back to disk with backup."""
    backup_file(filepath)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(workflow_dict, f, ensure_ascii=False, indent=2)

def list_api_scripts():
    """List installed scripts via API."""
    # Path asymmetry: POST uses /scripts (no /api), DELETE uses /api/scripts/{id}
    r = requests.get(f"{API_BASE}/scripts")
    r.raise_for_status()
    return r.json()

# NOTE: GET /scripts/{id} returns 404. Use list_api_scripts() and filter by
# name or id instead — the response data dict is keyed by script id.
# def get_api_script(script_id): ...  ← REMOVED: endpoint does not exist

RELOAD_SCRIPT = os.path.join(os.path.dirname(__file__), "scripts", "reload_gemphonefarm.py")

def reload_ui():
    """Reload GemPhoneFarm Electron window after API write."""
    if not os.path.exists(RELOAD_SCRIPT):
        print("[reload] Script not found. Press Cmd+R in GemPhoneFarm window.")
        return
    try:
        result = subprocess.run(
            [sys.executable, RELOAD_SCRIPT],
            capture_output=True, text=True, timeout=5
        )
        if result.stdout.strip() == "OK":
            print("[reload] GemPhoneFarm UI reloaded.")
        else:
            print(f"[reload] Failed: {result.stdout} {result.stderr}")
    except Exception as e:
        print("[reload] Error:", e)

def install_workflow(workflow_dict):
    """Install workflow via API. Deletes existing if same name exists."""
    # Check for existing
    scripts = list_api_scripts()
    for s in scripts:
        if s.get("name") == workflow_dict.get("name"):
            print(f"[delete] Removing existing: {s['name']} (id={s['id']})")
            requests.delete(f"{API_BASE}/api/scripts/{s['id']}")
    # Create new
    # Path asymmetry: POST /scripts (no /api prefix), DELETE /api/scripts/{id} (with /api)
    r = requests.post(f"{API_BASE}/scripts", json=workflow_dict)
    r.raise_for_status()
    print(f"[install] Created: {workflow_dict.get('name')}")
    reload_ui()  # MANDATORY
    return r.json()

def patch_node(workflow_dict, node_label, updates):
    """Find nodes by label and update their data fields."""
    nodes = workflow_dict["drawflow"]["nodes"]
    if isinstance(nodes, list):
        targets = [n for n in nodes if n.get("label") == node_label]
    else:
        targets = [n for n in nodes.values() if n.get("label") == node_label]
    for node in targets:
        node["data"].update(updates)
    return len(targets)

def build_node_map(workflow_dict):
    """Build {node_id: node} map regardless of nodes format."""
    nodes = workflow_dict["drawflow"]["nodes"]
    if isinstance(nodes, list):
        return {n["id"]: n for n in nodes}
    return nodes

def trace_path(workflow_dict, start_node_id, edge_filter=None):
    """Trace execution path from a node through edges."""
    node_map = build_node_map(workflow_dict)
    edges = workflow_dict["drawflow"]["edges"]
    path = [start_node_id]
    current = start_node_id
    while True:
        outgoing = [e for e in edges if e["source"] == current
                    and (edge_filter is None or edge_filter in e.get("sourceHandle", ""))]
        if not outgoing:
            break
        next_edge = outgoing[0]
        current = next_edge["target"]
        path.append(current)
    return [(nid, node_map.get(nid, {}).get("label", "?")) for nid in path]
```

---

## API/DB Shape Notes

### drawflow.nodes Format
- **extVersion "1.0.0"** (Boom, PAT, Boss): `nodes` is JSON array `[{...}, {...}]`
- **extVersion 2** (Jed, Jacob, Paji): `nodes` is JSON object `{"id1": {...}, "id2": {...}}` (on-disk)
- When building node maps, handle both: `isinstance(nodes, list)` check
- **API install**: always convert to array before `POST /scripts` — see Rule 4

### Edge Handle Naming
- Input port: `{nodeId}-input-1`
- Success output: `{nodeId}-output-1`
- Fallback output: `{nodeId}-output-fallback`
- Condition outputs: `{nodeId}-output-{conditionId}` (matches `data.conditions[].id`)
- Repeat-task loop output: `{nodeId}-output-2`

### Edge ID Convention
```
vueflow__edge-{sourceId}{sourceId}-output-1-{targetId}{targetId}-input-1
```
When adding new edges, follow this convention for consistency.

### settings Shape
```json
{
  "publicId": "",
  "blockDelay": 0,
  "saveLog": true,
  "debugMode": false,
  "restartTimes": 3,
  "notification": true,
  "execContext": "popup",
  "reuseLastState": false,
  "inputAutocomplete": true,
  "onError": "stop-workflow",
  "executedBlockOnWeb": false,
  "insertDefaultColumn": false,
  "defaultColumnName": "column"
}
```
Key fields: `blockDelay` (seconds between blocks), `onError` (`"stop-workflow"` | `"continue"`), `restartTimes` (auto-restart on failure).

### Encrypted Workflows
2 files use AES-256-CBC encryption (Base64, prefixed `U2FsdGVkX1`...):
- `PAT/watchShopeeLivebyURLs.GemPhoneFarm` (isProtected: true)
- `สคริปต์-Boom/JJK_Protected.GemPhoneFarm` (isProtected: true)

Cannot be edited without decryption key. Skip these.

### Platform Package Names Reference
| Platform | Package |
|----------|---------|
| Facebook | `com.facebook.katana` |
| Messenger | `com.facebook.orca` |
| Instagram | `com.instagram.android` |
| TikTok (intl) | `com.ss.android.ugc.trill` |
| TikTok (legacy) | `com.zhiliaoapp.musically` |
| X/Twitter | `com.twitter.android` |
| YouTube | `com.google.android.youtube` |
| Shopee | `com.shopee.th` |
| LINE | `jp.naver.line.android` |
| Lemon8 | `com.lemon8.android` |
| Grab | `com.grabtaxi.passenger` |
| Amazon | `com.amazon.mShop.android.shopping` |
| Google Maps | `com.google.android.apps.maps` |
| Google Play | `com.android.vending` |
| Chrome | `com.android.chrome` |
| FreeFire | `com.dts.freefireth` |
| Roblox | `com.roblox.client` |

---

## Editing Guidance

### When debugging "touch doesn't click"
1. Dump UI hierarchy from the exact screen state
2. Verify XPath matches a visible, clickable element
3. Check if element has `clickable="true"` in the hierarchy dump
4. Check if `waitForSelector` is true and `waitSelectorTimeout` is adequate
5. Verify the XPath is in `data.xPath` array (not `data.selector` — that's for type-text)
6. If element moves after scroll, re-dump after scroll action

### When debugging "workflow stops after conditions"
1. Map all condition IDs in `data.conditions[].id`
2. Map all outgoing edge `sourceHandle` values
3. Verify each handle matches: `{nodeId}-output-{conditionId}`
4. Missing handle match → `nextBlockId = null` → workflow stops silently

### When debugging "loop runs forever"
1. Check `loop-breakpoint` has correct `type: "BlockLoopBreakpoint"` and `label: "loop-breakpoint"`
2. Verify `data.loopId` matches the loop it should break
3. Check `repeat-task` output-2 edge routes back correctly
4. Verify counter variable is being incremented/depleted

### When adding new trigger parameters (extVersion 2)
1. Add to `workflow.trigger.parameters[]` (top-level)
2. Add same entry to trigger node `data.parameters[]` (inside drawflow)
3. Verify both arrays have matching `name`, `type`, `defaultValue`
4. After install, verify via MCP `gemphonefarm_list_scripts` or API `GET /scripts` (list all, find by name — `GET /scripts/{id}` returns 404)

### When changing submit logic
1. Trace every incoming and outgoing edge on the affected path
2. Remove duplicate submit side effects — if `press-key Enter` is the submit path, any JS submit on the same path must be removed
3. Keep `MAIN PATH` and `FALLBACK PATH` visually separated in layout

### When adding fallback recovery
1. Add fallback edge: `sourceHandle: "{id}-output-fallback"`, style: `"stroke: #ff6b6b"`
2. Fallback target: retry node, alternative approach node, or cleanup `end`
3. Update note blocks to explain the recovery path
4. Label fallback edges for readability at zoomed-out view

### When porting between extVersion formats
- v1.0.0 → v2: convert nodes array to object, add `"initialized": false` to each node (on-disk format)
- v2 → v1.0.0: convert nodes object to array, remove `"initialized"` field
- Test after conversion — some GemPhoneFarm versions may not handle mixed formats
- **Regardless of extVersion**: always convert nodes to array `[{...}]` before API `POST /scripts` install

---

## Trigger

Use when user asks to:
- "Edit/create/patch a GemPhoneFarm workflow"
- "Fix the TikTok/Facebook/IG/Shopee workflow"
- "Add a block to workflow X"
- "Change selector/timing/delay in workflow"
- "Debug why this workflow stops/fails/loops"
- "Port workflow from one platform to another"
- "Read what workflow X does"
- "Compare two workflows"
- "Build and install a workflow from spec"
- Any request involving `.GemPhoneFarm` files or GemPhoneFarm workflow JSON

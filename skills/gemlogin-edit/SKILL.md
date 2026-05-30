---
name: gemlogin-edit
description: Directly modify GemLogin workflows via its local SQLite database. Use when user asks to edit, batch update, rename, or change workflow logic in GemLogin by manipulating the db.db file directly.
---
# gemlogin-edit Skill

Directly modify GemLogin workflows via its local SQLite database.

## Path
Database: `C:\Users\pajipan\.gemlogin\db.db`
Workflows Table: `apps`
Reload Script: `scripts\reload_gemlogin.ps1` (bundled with this skill)

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
3. **Mandatory Reload UI**: After every database write (update, rename, delete), trigger GemLogin UI reload automatically. Use the bundled PowerShell script (`scripts\reload_gemlogin.ps1`). If the GemLogin window is not found, fall back to instructing the user to open DevTools (F12) and run `location.reload()`.
4. **Target IDs**: Use consistent node IDs (e.g., `open-url-node`) for easier automation.

## Scripts
- `scripts/reload_gemlogin.ps1` — Auto-reloads the GemLogin UI by focusing the window and sending `Ctrl+R`.
- `scripts/create_test_reload.py` — Inserts a minimal test workflow named `DevTools Test Reload` into `db.db`. Useful for verifying that the database write path and UI reload work together.

## Automation Script Template
Use Python to interact with the database and auto-reload the UI.

```python
import sqlite3, json, os, shutil, subprocess, sys
from datetime import datetime

DB_PATH = r"C:\Users\pajipan\.gemlogin\db.db"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RELOAD_PS1 = os.path.join(SCRIPT_DIR, "scripts", "reload_gemlogin.ps1")

def backup_db():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = DB_PATH.replace(".db", f"_bk_{ts}.db")
    shutil.copy2(DB_PATH, backup)
    return backup

def reload_gemlogin_ui():
    if not os.path.exists(RELOAD_PS1):
        print("[reload] Script not found. Open GemLogin DevTools (F12) and run location.reload()")
        return
    try:
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-File", RELOAD_PS1],
            capture_output=True, text=True, timeout=10
        )
        out = result.stdout.strip()
        if out == "OK":
            print("[reload] GemLogin UI reloaded.")
        elif out == "NOT_FOUND":
            print("[reload] GemLogin window not found. Open DevTools (F12) and run location.reload()")
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
    reload_gemlogin_ui()

def delete_workflow(name):
    backup_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM apps WHERE name = ?", (name,))
    conn.commit()
    conn.close()
    reload_gemlogin_ui()
```

## Trigger
Use when user asks to:
- "Edit workflow X in db"
- "Batch update GemLogin workflows"
- "Hack workflow logic directly"
- "Change start URL for all workflows"
- "Delete workflow X in GemLogin"

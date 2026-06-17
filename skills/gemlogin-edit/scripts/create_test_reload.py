import sqlite3
import json
import sys
from datetime import datetime
from pathlib import Path


def detect_db_path():
    if len(sys.argv) > 1:
        return sys.argv[1]
    home = Path.home()
    if sys.platform == "darwin":
        return str(home / ".gemlogin" / "db.db")
    return r"C:\Users\pajipan\.gemlogin\db.db"


db_path = detect_db_path()
app_id = "devtools-test-reload"
app_name = "DevTools Test Reload"


workflow = {
    "extVersion": "5.0.3",
    "name": app_name,
    "icon": "riPlayLine",
    "description": "Test Reload Workflow",
    "version": "1.0.0",
    "author": "Tester",
    "isProtected": False,
    "trigger": {
        "icon": "riPlayLine",
        "type": "manual",
        "parameters": []
    },
    "settings": {
        "blockDelay": 0,
        "saveLog": True
    },
    "drawflow": {
        "nodes": [],
        "edges": []
    },
    "id": app_id
}

now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + " +00:00"

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    script_json = json.dumps(workflow, ensure_ascii=False)
    
    cursor.execute("DELETE FROM apps WHERE id = ?", (app_id,))
    
    cursor.execute("""
        INSERT INTO apps (id, user_id, name, description, version, script, [table], input, enabale_input, metadata, expired_at, type, createdAt, updatedAt)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (app_id, None, app_name, "Empty test workflow", "1.0.0", script_json, "[]", None, None, None, None, "workflow", now_str, now_str))
    
    conn.commit()
    conn.close()
    print(f"Successfully inserted '{app_name}' into DB!")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)

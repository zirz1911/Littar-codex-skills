---
name: physical-setup
description: ตั้งค่า /physical ให้ดึง location ของตัวเอง — สำหรับ user ที่ติดตั้ง location tracking ไปแล้ว ใช้เมื่อพูดว่า physical setup, setup location skill, ตั้งค่า physical
user-invocable: true
---

# /physical-setup — Configure /physical for This Machine

ตั้งค่าให้ `/physical` ดึง location ของคุณเอง แทนที่จะเป็น default (paji)

## Steps

### Step 1: ถามข้อมูล

1. **Username** — "username ที่ใช้ตอน register location tracking คืออะไร?"
2. **GitHub repo** — "GitHub repo ที่เก็บ location data คืออะไร? (format: owner/repo เช่น yourname/my-location)"

### Step 2: เขียน config

```bash
python3 -c "
import json, os
config = {'username': '{username}', 'repo': '{github_repo}'}
path = os.path.expanduser('~/.claude/skills/physical/config.json')
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, 'w') as f:
    json.dump(config, f, indent=2)
print('Config saved:', path)
"
```

### Step 3: ทดสอบ

```bash
bun ~/.claude/skills/physical/scripts/location-query.ts current
```

ถ้าแสดง location ของคุณ → เสร็จแล้ว ✅

### Step 4: แสดงผล

```
✅ /physical configured!

จากนี้:
  /physical        → ดู location ของคุณ ({username})
  /physical paji   → ดู location ของ paji

Config: ~/.claude/skills/physical/config.json
```

## Notes

- Config ไฟล์นี้อยู่บนเครื่องของคุณเท่านั้น ไม่ได้ sync ไปที่อื่น
- เปลี่ยนได้ตลอดโดยรัน `/physical-setup` ใหม่

---
name: location-register
description: ลงทะเบียน Location Tracking ด้วยตัวเอง — ใช้ GitHub PAT ของ user เอง ใช้เมื่อพูดว่า location register, register location, ติดตั้ง location
user-invocable: true
---

# /location-register — Self-Register Location Tracking

ลงทะเบียน location tracking ด้วยตัวเอง โดยใช้ GitHub repo ของคุณเอง

## ต้องมีก่อน

1. **GitHub repo** สำหรับเก็บ location data (สร้างเองก่อน หรือ skill จะสร้างให้)
2. **GitHub PAT** (Personal Access Token) ที่มีสิทธิ์ `repo`
3. **Register Secret** — ขอจาก admin

## Steps

### Step 1: ถามข้อมูล (ทีละข้อ รอตอบก่อน)

1. **Username** — "ชื่อ username ที่ต้องการ? (ใช้สำหรับ login OwnTracks)"
2. **Password** — "ตั้ง password สำหรับ OwnTracks login"
3. **GitHub repo** — "ชื่อ GitHub repo ที่จะเก็บ location? (format: owner/repo เช่น yourname/my-location)"
   - ถ้า user ยังไม่มี repo: "สร้าง repo ใน GitHub ก่อนนะครับ: https://github.com/new — ตั้งชื่อ เช่น `my-location` แล้วแจ้งมา"
4. **GitHub PAT** — "GitHub Personal Access Token ที่มีสิทธิ์ `repo` — สร้างได้ที่ https://github.com/settings/tokens/new?scopes=repo"
5. **Register Secret** — "Register Secret จาก admin"

### Step 2: เรียก /register API

```bash
curl -s -X POST https://location.athena-oracle.site/register \
  -H "Content-Type: application/json" \
  -H "X-Register-Secret: {register_secret}" \
  -d '{
    "username": "{username}",
    "password": "{password}",
    "github_repo": "{github_repo}",
    "github_token": "{github_token}"
  }'
```

### Step 3: แสดงผล

ถ้า response มี `"status": "ok"` → เขียน config ลงเครื่องก่อน:

```bash
python3 -c "
import json, os
config = {'username': '{username}', 'repo': '{github_repo}'}
path = os.path.expanduser('~/.claude/skills/physical/config.json')
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, 'w') as f:
    json.dump(config, f, indent=2)
print('Config saved')
"
```

แล้วแสดง:

```
✅ ลงทะเบียนสำเร็จ!

📱 OwnTracks Settings:
─────────────────────
Mode:      HTTP
URL:       https://location.athena-oracle.site/pub
Username:  {username}
Password:  {password}
Device ID: iphone (หรืออะไรก็ได้)
TLS:       ON

📦 GitHub Repo: https://github.com/{github_repo}
```

ถ้า error:
- `409 already exists` → username นี้มีแล้ว เลือกชื่อใหม่
- `400 clone failed` → เช็ค github_repo URL และ PAT permissions
- `403 invalid secret` → register secret ผิด ขอใหม่จาก admin

## Notes

- PAT จะถูกเก็บบน server สำหรับ push location data เข้า repo
- ใช้ Fine-grained PAT จำกัดแค่ repo นั้นได้ที่ https://github.com/settings/personal-access-tokens/new
- "idle" ใน OwnTracks HTTP mode = ปกติ ไม่มี persistent connection
- ส่ง location จาก Map screen (ไม่ใช่ Publish Settings)

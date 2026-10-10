---
name: paji-summary
description: สรุปงานประจำวันแบบละเอียด — รวม raw data จาก paji-work collector + user context → บันทึกเป็น journal .md พร้อม timestamp ละเอียดเสมอ
---

# Paji-Summary — Daily Work Journal

สรุปงานแต่ละวันแบบละเอียด เก็บเป็น journal รายวัน

## Default Behavior (2026-07-07 update)

**Timestamp ละเอียดเสมอ** — ทุก section ต้องมีเวลา (HH:MM) กำกับ ไม่ต้องรอให้ user ขอ "แบบละเอียด"

- แต่ละบล็อกงาน: `### HH:MM — ชื่องาน`
- Bug แต่ละตัว: timestamp ที่เจอ
- Fix แต่ละรอบ: timestamp + ผลลัพธ์
- ตาราง "วิธีที่ลองแก้" ใส่เสมอเมื่อมีการ debug หลายรอบ
- ตาราง "📊 Final Stats" ใส่เมื่อจบโปรเจค/feature

## วิธีใช้

```
$paji-summary
$paji-summary วันนี้ทำอะไรมา
$paji-summary ช่วงเช้าทำ A ช่วงบ่ายประชุม ช่วงเย็นทำ B
```

## Pipeline

### Step 1: เก็บ raw data

```bash
cd /Users/pajipan/Desktop/Paji/project/paji-work/collector

.venv/bin/python -m paji_work_collector.cli scan-git
.venv/bin/python -m paji_work_collector.cli sessionize
.venv/bin/python -m paji_work_collector.cli summary
```

### Step 2: อ่าน session context

ไม่ต้องถาม user ถ้ามี context เพียงพอจาก:
- รอบ Codex session ปัจจุบัน (สิ่งที่เพิ่งทำ)
- Git commits ของวันนี้
- Wrap retrospectives ใน `Kvasir/memory/retrospectives/<today>/`
- Learnings ใน `Kvasir/memory/learnings/`

ถามเฉพาะเมื่อ context ไม่พอจริงๆ

### Step 3: อ่าน memory files

```bash
ls Kvasir/memory/learnings/ | grep $(date +%Y-%m-%d)
ls Kvasir/memory/retrospectives/$(date +%Y-%m)/ 2>/dev/null
```

### Step 4: สร้าง journal file

บันทึกที่ `/Users/pajipan/Desktop/Paji/project/paji-work/data/journal/YYYY-MM-DD.md`

## Output Template

```markdown
# YYYY-MM-DD — Daily Work Journal

**วัน:** <วัน> ที่ <เดือน> <ปี>
**เวลาเข้างาน:** <HH:MM> — <HH:MM> (active ~<นาที> นาที)
**สถานที่:** Bangkok (GMT+7)

---

## 📋 สรุปงาน

| ช่วงเวลา | งาน | สถานะ |
|----------|-----|--------|
| เช้า HH:MM-HH:MM | งาน A | ✅/🔴/🟡 |
| บ่าย HH:MM-HH:MM | งาน B | ✅/🔴/🟡 |

---

## 🌅 ช่วงเช้า — <หัวข้อ>

**เวลา:** HH:MM — HH:MM (active ~<นาที>)
**Tools:** <apps ที่ใช้>

---

### HH:MM-HH:MM — <งาน>

| เวลา | กิจกรรม |
|------|---------|
| HH:MM | <สิ่งที่ทำ> |
| HH:MM | <ขั้นตอนถัดไป> |

<รายละเอียดเพิ่มเติม>

**ผลลัพธ์:** ✅/🔴/🟡 <สรุป>

**Wrap commit:** `<hash>`

**Retrospective:** [filename.md](relative/path)

---

## 🔥 ช่วงบ่าย — <หัวข้อ>

**เวลา:** HH:MM — HH:MM (active ~<นาที>)
**Tools:** <apps ที่ใช้>

---

### HH:MM-HH:MM — <งานหลัก>

| เวลา | กิจกรรม |
|------|---------|
| HH:MM | <ขั้นตอน> |
| HH:MM | <ขั้นตอน> |

---

### 🐛 ปัญหาที่เจอ

**1. <ชื่อปัญหา>**
- **เวลา:** HH:MM
- **Root cause:** <สาเหตุ>
- **Fix:** <วิธีแก้>
- **ใช้ N iterations**

---

### 🔧 วิธีที่ลองแก้ (ถ้า ≥ 3 tries)

| # | เวลา | วิธี | ผล | ทำไมไม่เวิร์ค |
|---|------|------|-----|---------------|
| 1 | HH:MM | ... | ✅/❌/🟡 | ... |

---

### 📊 สถานะปัจจุบัน

| อย่าง | สถานะ |
|-------|--------|
| ... | ✅/🔴/🟡 |

---

### 📝 Files ที่แก้ไข (Littar-Codex)

| File | Change |
|------|--------|
| ... | ... |

### Files ที่แก้ไข (External)

| File | Change |
|------|--------|
| ... | ... |

### 📊 Final Stats (ถ้าจบ feature/project)

| Metric | Value |
|--------|-------|
| ... | ... |

---

### 📚 Knowledge Captured

**Learnings:**
- [filename.md](relative/path) — description

**Retrospectives:**
- [filename.md](relative/path)

---

## 🌆 ช่วงเย็น — Wrap-up

**เวลา:** HH:MM — HH:MM

- <สิ่งที่ทำ>

**Commits วันนี้:**

| เวลา | Commit | Message |
|------|--------|---------|
| HH:MM | `<hash>` | message |

---

## 📌 Next Steps

1. ...
2. ...
```

## Rules

- **Timestamp บังคับ:** ทุก section header ต้องมี `**เวลา:** HH:MM — HH:MM`
- **Granular time-activity:** ทุกงานย่อยต้องมี `| เวลา | กิจกรรม |` table — เลียนแบบ `2026-07-06.md`
- **ภาษา:** Thai ทั้งหมด ยกเว้น technical terms, file paths, code
- **วันเวลา:** Bangkok time (Asia/Bangkok)
- **ความยาว:** กระชับ แต่ครอบคลุม technical details + timestamps
- **สถานะ:** ✅ (เสร็จ), 🔴 (ยังไม่เสร็จ/พัง), 🟡 (ระหว่างทำ)
- **Technical details:** file paths, error messages, versions, commit hashes — ครบ
- **Bug format:** `**N. <ชื่อปัญหา>**` → `**เวลา:** HH:MM` → `**Root cause:**` → `**Fix:**` → `**ใช้ N iterations**`
- **Debug table:** ถ้ามีการลองแก้ ≥ 3 วิธี → ตาราง `🔧 วิธีที่ลองแก้` พร้อม timestamp
- **Final stats:** ถ้าจบ feature/project → ตาราง `📊 Final Stats`
- **📊 สถานะปัจจุบัน:** ใส่เสมอตอนจบแต่ละช่วง — list ทุกอย่างที่ทำวันนี้ + สถานะ
- **Commit table:** `| เวลา | Commit | Message |` — ทุก commit ของวัน
- **Files tables:** แยก `Littar-Codex` กับ `External` repos
- **Memory link paths:** relative path จาก `data/journal/` ไปหา `Kvasir/memory/`
- **ไม่ถามซ้ำ:** ใช้ session context + git + wraps + learnings ก่อนถาม user
- **Reference:** ดู `2026-07-06.md` เป็น gold standard format

## Related

- `paji-work` — raw summary (Bento Grid + Time Flow)
- `paji-summary` — detailed journal with timestamps (this skill)
- `wrap` — session retrospective + Kvasir memory commit

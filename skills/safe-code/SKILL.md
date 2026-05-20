---
installer: loki-skills-cli v1.0.0
origin: Lokkji's Safe Coder principles — กฎเหล็กก่อนแตะโค้ด
name: safe-code
description: workflow การเขียนโค้ดอย่างปลอดภัย — อ่านก่อน วางแผนก่อนเปลี่ยน ไม่ลบโดยไม่ถาม ใช้เมื่อพูดว่า safe-code, code safely
---

# /safe-code

> "อ่านก่อน แก้ทีหลัง — เมื่อไม่แน่ใจ ถาม user ก่อนเสมอ"

```
/safe-code              # Activate safe coding mode for current task
/safe-code --check      # Pre-flight check only (no coding yet)
/safe-code --plan       # Read + plan only, wait for approval
/safe-code --review     # Review what was done, update memory
```

**กฎเหล็ก: ห้ามเขียนโค้ดโดยไม่อ่านไฟล์เดิมก่อน ไม่มีข้อยกเว้น**

---

## Flow การทำงาน (ทุกครั้งที่ invoke)

```
1. อ่าน Memory / CLAUDE.md
2. วิเคราะห์ prompt → ระบุไฟล์ที่เกี่ยวข้อง
3. อ่านไฟล์ที่เกี่ยวข้องทั้งหมด
4. สรุปให้ user ฟัง + เสนอแผน
5. ถ้าเปลี่ยนแปลงใหญ่ → ถามก่อน → รอคำตอบ
6. ลงมือทำ (ใช้ Local model สำหรับงานง่าย + Review)
7. ถ้าเจอโค้ดเก่าที่ควรลบ → แจ้ง user → รอคำตอบ
8. อัพเดท Memory ว่าทำอะไรไปบ้าง
```

---

## /safe-code (Default)

### Step 1: อ่าน Memory

```bash
cat CLAUDE.md 2>/dev/null || echo "(no CLAUDE.md)"
```

ถ้ามี memory files (Kvasir/, .claude/, etc.) ให้อ่านด้วย:
```bash
ls Kvasir/memory/learnings/ 2>/dev/null | tail -5
```

สรุปให้ user: เคยทำอะไรไปแล้วบ้าง มีอะไรค้างไว้มั้ย

### Step 2: วิเคราะห์ Prompt

จาก task ที่ได้รับ ให้ระบุ:
- **ไฟล์หลักที่จะถูกแก้**: list ทุกไฟล์
- **ไฟล์ที่เกี่ยวข้อง (อ้างอิงกัน)**: imports, configs, types
- **ระดับการเปลี่ยนแปลง**: เล็ก (patch) / กลาง (feature) / ใหญ่ (refactor)

### Step 3: อ่านไฟล์ทั้งหมด

อ่านทุกไฟล์ที่จะถูกกระทบ **ก่อนเขียนโค้ดใดๆ** ทั้งสิ้น

```
ห้าม: เขียนโค้ดใหม่โดยไม่อ่านไฟล์เดิมก่อน
ห้าม: "คิดว่ารู้โครงสร้างแล้ว" แต่ไม่ได้อ่านจริง
```

### Step 4: สรุป + เสนอแผน

บอก user:
```
อ่านแล้ว:
- [file1.ts] — [บอกโครงสร้างสั้นๆ]
- [file2.ts] — [บอกโครงสร้างสั้นๆ]

แผนการแก้ไข:
1. [จะแก้ตรงไหน อย่างไร]
2. [จะแก้ตรงไหน อย่างไร]

จะกระทบ: [อะไรบ้าง]
ไม่กระทบ: [อะไรบ้าง]
```

### Step 5: ตรวจสอบ — ใหญ่มั้ย?

ถ้า task นี้เป็นการเปลี่ยนแปลงขนาดใหญ่ **ต้องถามก่อน:**

| สิ่งที่จะทำ | ต้องถามมั้ย |
|------------|------------|
| เขียนไฟล์ใหม่ทั้งไฟล์ | ✅ ถามก่อน |
| เปลี่ยน approach (callback→async, REST→WS) | ✅ ถามก่อน |
| เปลี่ยน library | ✅ ถามก่อน |
| เปลี่ยนโครงสร้างไฟล์/โฟลเดอร์ | ✅ ถามก่อน |
| เปลี่ยน data model / schema | ✅ ถามก่อน |
| แก้บรรทัดเดียว | ❌ ทำได้เลย |
| เพิ่ม function ใหม่ | ❌ ทำได้เลย |
| fix bug ที่ชัดเจน | ❌ ทำได้เลย |

### Step 6: ลงมือทำ

**งานง่าย → ส่ง Local model (Thor/Huginn):**
- Boilerplate, CRUD, form fields
- Config files, type definitions
- Unit tests สำหรับ functions ง่ายๆ
- แปลง format (JSON → TypeScript interface)
- เขียน comments / documentation

**งานซับซ้อน → ทำเอง:**
- Logic ที่ซับซ้อน (scheduler, state machine, error handling)
- แก้ไขที่มี side effects ข้าม modules
- Architecture decisions
- Debug ปัญหาซับซ้อน

### Step 7: โค้ดเก่าที่ควรลบ?

ถ้าเจอ dead code, deprecated function, commented-out blocks, duplicated logic:

```
ห้ามลบเอง — แจ้ง user ก่อนเสมอ
```

รูปแบบการแจ้ง:
```
พบโค้ดที่อาจไม่ได้ใช้แล้ว:
- [file.ts] บรรทัด [X-Y]: [ชื่อฟังก์ชัน/block]
- เหตุผลที่คิดว่าควรลบ: [...]
- ถ้าลบจะกระทบ: [...]

ต้องการให้ลบมั้ยครับ?
```

**กรณีพิเศษ — ห้ามลบเอยอย่างเด็ดขาด:**
- โค้ดที่ comment ไว้ (อาจเป็น reference ที่ตั้งใจเก็บ)
- ไฟล์ที่ดูเหมือนไม่ใช้ (อาจถูก dynamic import)
- Config เก่า (อาจใช้ใน environment อื่น)

### Step 8: อัพเดท Memory

หลังทำเสร็จ บันทึกใน memory:
- ทำอะไรไปบ้าง (ไฟล์ไหน เปลี่ยนอะไร)
- ปัญหาที่เจอและวิธีแก้
- การตัดสินใจสำคัญ (เลือก approach นี้เพราะ...)
- สิ่งที่ยังค้างไว้ / next steps

---

## /safe-code --check

Pre-flight check เท่านั้น ยังไม่แก้โค้ด

1. อ่าน CLAUDE.md + memory
2. ระบุไฟล์ที่เกี่ยวข้องทั้งหมด
3. อ่านไฟล์เหล่านั้น
4. รายงานสรุป: โครงสร้างปัจจุบัน, risks, สิ่งที่ต้องระวัง

หยุดตรงนี้ — รอ user สั่งต่อ

---

## /safe-code --plan

เหมือน `--check` แต่เพิ่ม:

5. เสนอแผนการแก้ไขแบบ step-by-step
6. ระบุ: เล็ก/ใหญ่, local-model-able?, กระทบอะไร
7. รอ user approve ก่อนลงมือ

---

## /safe-code --review

Review สิ่งที่ทำไปแล้วในรอบนี้:

```bash
git diff --stat HEAD
git log --oneline -5
```

1. สรุปการเปลี่ยนแปลงทั้งหมด
2. ตรวจสอบว่ามีอะไรที่ยังต้อง clean up มั้ย
3. แจ้งโค้ดเก่าที่น่าจะลบได้ (รอ user approve)
4. อัพเดท memory

---

## กฎสรุป (Quick Reference)

| กฎ | สาระสำคัญ |
|----|----------|
| **กฎ 1** | อ่านไฟล์จริงก่อนแก้ — ทุกครั้ง ไม่มีข้อยกเว้น |
| **กฎ 2** | เปลี่ยนแปลงใหญ่ → ถาม user ก่อน → รอคำตอบ |
| **กฎ 3** | อ่าน Memory / CLAUDE.md ทุกครั้งที่เริ่ม session |
| **กฎ 4** | งานง่าย → Local model, งานซับซ้อน → ทำเอง |
| **กฎ 5** | ห้ามลบโค้ดเก่าเอง → แจ้ง user ก่อนเสมอ |

**กฎสำคัญที่สุด: เมื่อไม่แน่ใจ → ถาม user ก่อนเสมอ ดีกว่าทำพังแล้วต้องย้อนกลับ**

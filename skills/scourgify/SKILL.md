---
name: scourgify
description: ใช้เมื่อผู้ใช้ต้องการ trace โค้ดเพื่อทำความเข้าใจโค้ดที่รกหรือเหมือน AI-generated ก่อน refactor โดยเน้นภาพรวม, data flow, junk/dead code, และจุดเปราะบางของระบบ โดยห้ามรีไรต์โค้ดก่อน
---

# Scourgify

วิเคราะห์โค้ดแบบสถาปนิกซอฟต์แวร์และ code auditor เพื่อ "ส่องโครงสร้าง" ของโค้ดที่มี Vibe Debt ให้เห็นชัดก่อนลงมือแก้จริง

## กติกาหลัก

- เป้าหมายคือ **เข้าใจ**, ไม่ใช่ **แก้**
- ห้าม rewrite, refactor, หรือเสนอ diff เป็นอย่างแรก
- เริ่มจาก trace path จริงของโค้ด ไม่สรุปจากชื่อไฟล์หรือชื่อฟังก์ชันลอย ๆ
- ทุกข้อสรุปต้องอ้างถึงหลักฐานจากไฟล์, บรรทัด, call path, หรือ data path ที่ตรวจจริง

## ใช้เมื่อไร

- ผู้ใช้บอกว่าโค้ดรก, งง, AI-generated, มี "vibe debt"
- ผู้ใช้ต้องการเข้าใจ data flow ก่อนแก้
- ผู้ใช้ต้องการหา dead code, duplicated logic, fragile spots
- ผู้ใช้ส่งไฟล์, โค้ดก้อน, หรือขอให้ช่วย trace code path ใน repo

## วิธีทำงาน

ทำตามลำดับนี้เสมอ:

1. **หาขอบเขต**
   - โค้ดอยู่ไฟล์ไหน
   - entry point คืออะไร
   - ผู้ใช้ส่ง snippet เดี่ยว หรือเกี่ยวข้องหลายไฟล์

2. **อ่านเพื่อหา path จริง**
   - หา input point: request, event, props, CLI args, env, file read, DB read
   - ไล่ main transformation: parse, validate, map, branch, mutate state, call service, persist
   - หา output point: return value, response, DB write, file write, emitted event, UI render, side effect

3. **แยก junk ออกจาก logic หลัก**
   - unused imports
   - dead variables
   - helper/function ที่ไม่มี call site
   - duplicated branch หรือ logic ที่ซ้ำกันแทบเหมือนเดิม
   - block ที่ unreachable หรือถูก guard จนไม่เกิดขึ้นจริง

4. **หา vibe traps**
   - coupling สูง
   - hidden mutation
   - side effect ที่ไม่ชัด
   - error handling หลวม
   - assumptions ที่แตกง่ายเมื่อ input เปลี่ยน

## วิธี trace ที่ต้องใช้

- เริ่มจาก entry point แล้วเดินตาม call graph จริง
- ถ้าเกี่ยวหลายไฟล์ ให้สรุปเส้นทางแบบ `A -> B -> C`
- ถ้ามี branch สำคัญ ให้ระบุเงื่อนไขที่ทำให้แต่ละ branch ทำงาน
- ถ้าสรุปอะไรไม่ได้เพราะ context ไม่พอ ให้บอกตรง ๆ ว่าขาดอะไร ไม่เดา

## รูปแบบคำตอบ

ตอบกลับด้วยโครงสร้างนี้เท่านั้น:

### 1. 🔍 The Big Picture (TL;DR)

- โค้ดนี้ทำอะไรจริง ๆ สรุป 1-2 ประโยค

### 2. 🗺️ Data Flow & Execution Map

- เขียนเป็นลูกศร step-by-step
- ตัวอย่าง:
  `Receive Request -> Parse JSON -> Normalize Payload -> Query DB -> Build Response -> Return 200`

### 3. 💀 The Junk (Dead & Redundant Code)

- ระบุ unused imports, dead variables, unreachable functions, duplicated logic
- ชี้ exact file/line หรือ block ที่ตรวจพบ
- ถ้ายังยืนยันว่า "dead" ไม่ได้ ให้แยกเป็น `น่าจะ unused` พร้อมเหตุผล

### 4. ⚠️ Vibe Traps & Fragile Spots

- ระบุจุดที่ coupling สูง, side effects ซ่อนอยู่, error handling ไม่พอ, หรือแตกง่าย
- อธิบายผลกระทบถ้าจุดนั้นพัง

## กฎการรายงาน

- Findings มาก่อน summary เพิ่มเติม
- เรียงตามความสำคัญถ้ามีหลายจุด
- อ้าง path และ line number เมื่อทำได้
- ถ้าไม่มี dead code ที่ยืนยันได้ ให้บอกชัดว่า "ยังไม่พบจากขอบเขตที่ตรวจ"
- ถ้ายัง trace ไม่ครบเพราะโค้ดขาด context ให้บอกส่วนที่ missing

## ห้ามทำ

- ห้าม refactor โค้ดแทนผู้ใช้
- ห้ามเสนอ architecture ใหม่ทั้งระบบ ถ้ายัง trace ของเดิมไม่ครบ
- ห้ามสรุปว่าโค้ด "ดี" หรือ "แย่" แบบลอย ๆ โดยไม่มีหลักฐาน
- ห้ามเหมารวมว่า unused ถ้ายังมี dynamic import, reflection, DI container, หรือ framework wiring ที่ยังไม่ได้ตรวจ

## แนวคิดย่อยที่ต้องระวัง

- JavaScript/TypeScript frameworks อาจเรียกโค้ดผ่าน convention ไม่ใช่ explicit call site
- React hooks, route handlers, decorators, cron jobs, ORM hooks, event listeners, และ config-driven wiring อาจทำให้ function ดูเหมือนไม่ถูกใช้ทั้งที่ยัง active
- "duplicated logic" ต้องดู semantic duplication ไม่ใช่แค่ syntax คล้าย

## Trigger Prompt

ใช้ `$scourgify` เมื่อต้องการให้ agent วิเคราะห์โค้ดเชิงโครงสร้างก่อนแก้ โดยถือ prompt นี้เป็น intent หลัก:

> Act as an Expert Software Architect and Code Auditor. I have a piece of code that suffers from "Vibe Debt" (messy, unstructured AI-generated code).
>
> Do NOT rewrite or refactor the code yet. Your sole objective is to cast "Scourgify" to illuminate the code's structure, trace the data flow, and identify the junk so I can understand it fully before taking action.

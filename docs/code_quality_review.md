# 🔍 ALM-X-IMPACT Tennis — Backend Code Quality Review

> **วันที่ตรวจ:** 29 พฤษภาคม 2026
> **ตรวจสอบ:** โค้ดทั้งหมด 15 ไฟล์ + เอกสาร MASTER_PLAN.md

---

## 📊 สรุปภาพรวม

| ระดับ | จำนวน | คำอธิบาย |
|-------|--------|----------|
| 🔴 Critical | 7 | บั๊กหรือปัญหาที่ส่งผลต่อการทำงานหรือความปลอดภัยโดยตรง |
| 🟡 Moderate | 8 | ปัญหาด้านโครงสร้าง/คุณภาพที่ควรแก้ก่อนเปิดใช้งานจริง |
| 🟢 Minor | 6 | เรื่องเล็กน้อย/ปรับปรุงเพิ่มเติมได้ |

---

## 🔴 Critical Issues (7 รายการ)

### C1. `datetime.utcnow()` deprecated ตั้งแต่ Python 3.12+
- **ไฟล์:** [models.py](file:///c:/GitHub/ALM-X-IMPACT-Tennis/backend/app/models.py#L38), [data_service.py](file:///c:/GitHub/ALM-X-IMPACT-Tennis/backend/app/services/data_service.py#L62), [utils.py](file:///c:/GitHub/ALM-X-IMPACT-Tennis/backend/app/utils.py#L25), [main.py](file:///c:/GitHub/ALM-X-IMPACT-Tennis/backend/main.py#L92)
- **ปัญหา:** `datetime.utcnow()` ถูกใช้กว่า **15+ แห่ง** ทั่วทั้งโปรเจกต์ ฟังก์ชันนี้ deprecated ใน Python 3.12 และจะถูกลบในอนาคต ไม่ใส่ timezone ทำให้เวลาไม่มี awareness
- **แนะนำ:** เปลี่ยนเป็น `datetime.now(timezone.utc)` ทั้งหมด

### C2. `@app.on_event("startup")` deprecated ใน FastAPI
- **ไฟล์:** [main.py:57](file:///c:/GitHub/ALM-X-IMPACT-Tennis/backend/main.py#L57)
- **ปัญหา:** FastAPI 0.115.6 ที่ใช้อยู่ แนะนำให้ใช้ `lifespan` context manager แทน `on_event("startup")` เนื่องจากถูก deprecated
- **แนะนำ:** เปลี่ยนไปใช้ `@asynccontextmanager async def lifespan(app)`

### C3. ระบบสถาปัตยกรรมคู่ขนาน: Mock DB vs Beanie — ไม่มีการสลับที่ชัดเจน
- **ไฟล์:** [data_service.py](file:///c:/GitHub/ALM-X-IMPACT-Tennis/backend/app/services/data_service.py), [main.py](file:///c:/GitHub/ALM-X-IMPACT-Tennis/backend/main.py#L60-L68)
- **ปัญหาหลัก:** ระบบตอนนี้มี **สองระบบฐานข้อมูลทำงานพร้อมกัน** แต่ไม่ได้เชื่อมโยงกัน:
  1. `main.py` startup → connect MongoDB + init Beanie + seed Users/Courts **ลง MongoDB จริง** ✅
  2. **แต่ทุก Router** ยังเรียก `DataService` ซึ่ง **อ่าน/เขียนจาก `mock_db.py` (In-Memory Dictionary)** เท่านั้น ❌
- **ผลกระทบ:** ข้อมูล 767 คนที่ seed เข้า MongoDB ไม่ถูกใช้งานจริง — ทุก API ยังทำงานจากข้อมูลจำลอง 3 คน
- **แนะนำ:** ต้องเลือกทางใดทางหนึ่ง:
  - (A) เขียน `DataService` ใหม่ให้ query ผ่าน Beanie models (ใช้ MongoDB จริง)
  - (B) หรือทำ flag environment `USE_MOCK_DB=true/false` ให้สลับได้

### C4. `httpx` ไม่ได้อยู่ใน requirements.txt
- **ไฟล์:** [sms_service.py](file:///c:/GitHub/ALM-X-IMPACT-Tennis/backend/app/services/sms_service.py#L1), [data_service.py](file:///c:/GitHub/ALM-X-IMPACT-Tennis/backend/app/services/data_service.py#L133)
- **ปัญหา:** ใช้ `import httpx` สำหรับ SMS OTP แต่ไม่ได้ระบุใน [requirements.txt](file:///c:/GitHub/ALM-X-IMPACT-Tennis/backend/requirements.txt) ทำให้ Docker build ติดตั้งไม่ครบ — จะ crash ตอนยิง OTP จริง
- **แนะนำ:** เพิ่ม `httpx` ใน `requirements.txt`

### C5. Error ใน startup ถูก catch แต่แอปไม่หยุดทำงาน
- **ไฟล์:** [main.py:146](file:///c:/GitHub/ALM-X-IMPACT-Tennis/backend/main.py#L146)
- **ปัญหา:** ถ้า MongoDB เชื่อมต่อไม่ได้ หรือ seed ข้อมูลพัง ระบบแค่ `logger.error()` แล้ว**ทำงานต่อ** โดยที่ Beanie models ไม่ได้ init — ทำให้ทุก Beanie query จะ crash เมื่อมีคนเรียก API ที่ใช้ MongoDB
- **แนะนำ:** ควร raise error หรือ set flag ให้ API ตอบ 503 เมื่อ DB ไม่พร้อม

### C6. SMS OTP ส่ง `otp_code` กลับใน Response แบบจำลอง + print ใน console
- **ไฟล์:** [auth.py:185](file:///c:/GitHub/ALM-X-IMPACT-Tennis/backend/app/routers/auth.py#L185)
- **ปัญหา:** ใน Simulator mode ระบบ `print()` OTP code ลง console ซึ่ง Docker logs ดูได้ง่าย → ต้องลบ/ปิดก่อน production
- **แนะนำ:** ใช้ `logger.debug()` แทน `print()` และปิด debug level บน production

### C7. `StorageService.upload_slip()` เป็น Synchronous ใน Async Endpoint
- **ไฟล์:** [payments.py:21](file:///c:/GitHub/ALM-X-IMPACT-Tennis/backend/app/routers/payments.py#L21), [storage_service.py:49-51](file:///c:/GitHub/ALM-X-IMPACT-Tennis/backend/app/services/storage_service.py#L49-L51)
- **ปัญหา:** Endpoint `upload_payment_slip` เป็น `async def` แต่ภายในเรียก `shutil.copyfileobj()` ซึ่งเป็น **blocking I/O** → จะบล็อก event loop ทำให้ server ไม่ตอบ request อื่นระหว่างเขียนไฟล์
- **แนะนำ:** ใช้ `await asyncio.to_thread(...)` หรือ `aiofiles` แทน

---

## 🟡 Moderate Issues (8 รายการ)

### M1. Import ระเกะ — ไม่เป็นระเบียบใน `main.py`
- **ไฟล์:** [main.py](file:///c:/GitHub/ALM-X-IMPACT-Tennis/backend/main.py)
- **ปัญหา:** Import กระจายอยู่ทั่วไฟล์ (บรรทัด 1-12, 18, 30, 54, 61, 74-75) แทนที่จะรวมไว้ด้านบน
- **แนะนำ:** จัดกลุ่ม import ให้เป็นระเบียบตาม PEP 8 ที่ด้านบนของไฟล์

### M2. `logging.basicConfig()` ถูกเรียกหลัง `setup_logging()`
- **ไฟล์:** [main.py:15-21](file:///c:/GitHub/ALM-X-IMPACT-Tennis/backend/main.py#L15-L21)
- **ปัญหา:** `setup_logging()` ตั้งค่า root logger เสร็จแล้ว แต่บรรทัด 21 เรียก `logging.basicConfig(level=logging.INFO)` อีกรอบ → อาจเพิ่ม handler ซ้ำ
- **แนะนำ:** ลบ `logging.basicConfig()` ออก เพราะ `setup_logging()` จัดการครบแล้ว

### M3. Custom Exceptions สร้างไว้แต่ไม่ได้ใช้งาน
- **ไฟล์:** [exceptions.py](file:///c:/GitHub/ALM-X-IMPACT-Tennis/backend/app/exceptions.py)
- **ปัญหา:** `SlotConflictException` และ `UserDuplicateBookingException` ถูกประกาศไว้ แต่ใน [queues.py](file:///c:/GitHub/ALM-X-IMPACT-Tennis/backend/app/routers/queues.py) ใช้ `HTTPException` ตรงๆ แทน
- **แนะนำ:** เลือกทางใดทางหนึ่ง — ใช้ Custom Exceptions + Exception Handler หรือลบ exceptions ที่ไม่ได้ใช้ออก

### M4. ไม่มี Exception Handler สำหรับ `ALMException`
- **ไฟล์:** [main.py](file:///c:/GitHub/ALM-X-IMPACT-Tennis/backend/main.py)
- **ปัญหา:** `SMSGatewayException` อาจถูก raise จาก `sms_service.py` / `data_service.py` แต่ไม่มี `@app.exception_handler(ALMException)` จัดการ → จะกลายเป็น 500 Internal Server Error แทน 502
- **แนะนำ:** เพิ่ม global exception handler ใน `main.py`

### M5. ไม่มี Database Index Definitions ใน Beanie Models
- **ไฟล์:** [models.py](file:///c:/GitHub/ALM-X-IMPACT-Tennis/backend/app/models.py)
- **ปัญหา:** ไม่มี Index สำหรับ:
  - `User.email` (unique) — ตรวจอีเมลซ้ำจะช้าเมื่อข้อมูลเยอะ
  - `Booking(court_id, booking_date, time_slot)` (compound) — ตรวจ slot conflict จะช้า
- **แนะนำ:** เพิ่ม `class Settings` ใน models กำหนด `indexes`

### M6. `payments.py` ไม่ตรวจสอบว่า `booking_id` มีจริงก่อนสร้าง Transaction
- **ไฟล์:** [payments.py:23](file:///c:/GitHub/ALM-X-IMPACT-Tennis/backend/app/routers/payments.py#L23)
- **ปัญหา:** รับ `booking_id` จาก form แล้วส่งตรงไป `create_transaction()` โดยไม่ตรวจว่า booking นี้มีอยู่จริงหรือเป็นของ user คนนี้หรือไม่
- **แนะนำ:** เพิ่ม guard ตรวจ `DataService.get_booking_by_id(booking_id)` + ตรวจ ownership

### M7. `data_service.py` Verify OTP มี Business Logic ปนกับ HTTP Call
- **ไฟล์:** [data_service.py:102-171](file:///c:/GitHub/ALM-X-IMPACT-Tennis/backend/app/services/data_service.py#L102-L171)
- **ปัญหา:** `verify_otp()` ในคลาส `DataService` (ที่ควรเป็น data layer) มี `httpx.Client().post()` เรียก ThaiBulkSMS API โดยตรง → ละเมิด Separation of Concerns
- **แนะนำ:** ย้าย logic verification ผ่าน API ไปไว้ใน `sms_service.py` แยกออกจาก data layer

### M8. `seeded_users.json` (565 KB) ถูกโหลดสองครั้ง
- **ไฟล์:** [mock_db.py:186-198](file:///c:/GitHub/ALM-X-IMPACT-Tennis/backend/app/services/mock_db.py#L186-L198), [main.py:79-114](file:///c:/GitHub/ALM-X-IMPACT-Tennis/backend/main.py#L79-L114)
- **ปัญหา:** ไฟล์ 565KB ถูกอ่านและ parse JSON สองครั้งตอนเปิดเซิร์ฟเวอร์:
  1. `mock_db.py` → โหลดเข้า In-Memory Dictionary (module-level)
  2. `main.py` startup → โหลดเข้า MongoDB ผ่าน Beanie
- **ผลกระทบ:** เปลือง memory + startup time ช้า
- **แนะนำ:** โหลดเพียงครั้งเดียว ตามแนวทาง C3

---

## 🟢 Minor Issues (6 รายการ)

### L1. `docker-compose.yml` ไม่มี `version` (ถูกลบไปแล้วดี — แต่ตอนก่อนหน้ายังเหลือ warning)
- สถานะ: ✅ แก้แล้ว (ไม่มี `version` field)

### L2. `Court.available_slots` เก็บ hardcoded time_slot — ไม่ dynamic
- **ปัญหา:** เวลาสล็อตถูก hardcode เป็น 5 ช่วง (16:00-21:00) ต่อสนาม ไม่มีระบบให้ admin แก้ไขได้
- **แนะนำ:** ในอนาคตควรมี endpoint ให้ admin จัดการ slot

### L3. Response Models ไม่ได้ใช้ Pydantic `response_model`
- **ปัญหา:** ส่วนใหญ่ return `dict` ตรงๆ → Swagger docs ไม่แสดง response schema ชัดเจน
- **แนะนำ:** สร้าง Pydantic response models สำหรับ endpoint สำคัญ

### L4. Tests (`test_integration.py`, `test_edge_cases.py`) ไม่ได้ตรวจสอบในรอบนี้
- **หมายเหตุ:** ไม่ได้รัน pytest ตรวจ ควรรัน unit test อีกครั้งหลังแก้ไข

### L5. ไฟล์ `.env` มี SMS API Credentials จริง hardcode อยู่
- **ไฟล์:** [.env:15-16](file:///c:/GitHub/ALM-X-IMPACT-Tennis/backend/.env#L15-L16)
- **ปัญหา:** `SMS_API_KEY` และ `SMS_API_SECRET` ค่าจริงอยู่ใน repo — ถ้า push ขึ้น public GitHub จะรั่วไหล
- **แนะนำ:** ตรวจ `.gitignore` ว่ามี `.env` อยู่แล้ว ✅ (มีอยู่แล้ว) แต่ถ้า commit ไปก่อนหน้าก็ต้อง revoke key

### L6. Logging format ซ้ำซ้อน
- **ปัญหา:** ทั้ง `setup_logging()` และ `logging.basicConfig()` ตั้ง format → อาจมี double log lines
- **เกี่ยวข้อง:** M2

---

## 📋 เอกสาร vs โค้ด — ความสอดคล้อง

### MASTER_PLAN.md — จุดที่ **ไม่ตรงกับโค้ดจริง**

| # | รายการในเอกสาร | สถานะในเอกสาร | สถานะจริง | ปัญหา |
|---|----------------|---------------|-----------|-------|
| 1 | ส่วน 2.1 #1: `init_beanie()` ใน startup event | ❌ ยังไม่ได้ทำ | **✅ ทำแล้ว** | เอกสารไม่ได้อัปเดต — `main.py` มี `init_beanie()` + seed เรียบร้อยแล้ว |
| 2 | ส่วน 2.1 #4: สร้าง Database Seed Script | ❌ ยังไม่ได้ทำ | **✅ ทำแล้ว** | Seed logic อยู่ใน `main.py` startup (ไม่ใช่ script แยก แต่ทำงานอัตโนมัติ) |
| 3 | ส่วน 2.2 #2: สร้าง `storage_service.py` | ❌ ยังไม่ได้ทำ | **✅ มีแล้ว** | ไฟล์ [storage_service.py](file:///c:/GitHub/ALM-X-IMPACT-Tennis/backend/app/services/storage_service.py) มีอยู่แล้วและทำงานได้ |
| 4 | ส่วน 2.2 #3: แก้ไข `payments.py` ให้อัปโหลดจริง | ❌ ยังไม่ได้ทำ | **✅ แก้แล้ว** | [payments.py](file:///c:/GitHub/ALM-X-IMPACT-Tennis/backend/app/routers/payments.py) เรียก `StorageService.upload_slip()` แล้ว |
| 5 | ส่วน 0.4: เอกสารบอกว่า `storage_service.py` เสร็จแล้ว ✅ | ✅ | ✅ | ตรงกัน (สอดคล้อง) |
| 6 | ส่วน 2.1 #2: เปลี่ยน DataService → Beanie queries | ❌ ยังไม่ได้ทำ | **❌ จริง ยังไม่ได้ทำ** | ตรงกับเอกสาร — DataService ยังใช้ mock dictionary |
| 7 | ส่วน 2.1 #3: Routers เรียก mock โดยตรง | ❌ ยังไม่ได้ทำ | **🟡 บางส่วน** | `courts.py` เรียกผ่าน `DataService` แล้ว (ไม่ได้เรียก mock โดยตรง) แต่ DataService ยังใช้ mock อยู่ดี |

### สรุปเอกสาร
- **MASTER_PLAN.md ล้าสมัยไปหลายจุด** — ส่วนที่ 2.1 #1, 2.2 #2-3 ทำเสร็จแล้วแต่เอกสารยังบอก ❌
- **จำนวนรายการสรุป** ไม่ตรง: เอกสารบอก Phase 1.5 มี 0 เสร็จ → ตอนนี้มี 3-4 รายการที่ทำเสร็จแล้ว
- **ไม่มีการบันทึก Docker setup** ในเอกสารไหนเลย (Dockerfile, docker-compose.yml ไม่ถูกกล่าวถึง)

---

## 🏗️ Docker Status — ✅ ทำงานสำเร็จ

```
✅ mongodb-tennis  — MongoDB เปิดทำงาน พร้อมรับ connections
✅ backend-tennis  — FastAPI เปิดทำงาน port 8000
✅ Database Seed   — นำเข้าผู้ใช้ 767 คน + สนาม 2 คอร์ทลง MongoDB สำเร็จ
✅ Uvicorn         — running on http://0.0.0.0:8000
```

---

## 🎯 ลำดับการแก้ไขที่แนะนำ

```
Priority 1 (ก่อน Production):
├─ C3: เลือกทิศทาง Mock vs MongoDB → เขียน DataService ใหม่
├─ C4: เพิ่ม httpx ใน requirements.txt
├─ C5: จัดการ startup failure ให้ไม่ทำให้ API ค้างระหว่างทาง
└─ M6: ตรวจ booking_id ก่อนสร้าง transaction

Priority 2 (ก่อน Scale):
├─ C1: แก้ datetime.utcnow() → datetime.now(timezone.utc)
├─ C2: เปลี่ยนเป็น lifespan context manager
├─ C7: ใช้ async file I/O
└─ M5: เพิ่ม database indexes

Priority 3 (อัปเดตเอกสาร):
├─ อัปเดต MASTER_PLAN.md ส่วน 2.1, 2.2 ให้ตรงสถานะจริง
├─ เพิ่มส่วน Docker Infrastructure ในเอกสาร
└─ อัปเดตตารางสรุปสถานะรวม
```

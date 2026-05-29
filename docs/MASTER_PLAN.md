# 🗺️ ALM-X-IMPACT Tennis — Backend Master Plan
> **เอกสารแผนงานหลักฝั่งหลังบ้าน (Backend Roadmap & Checklist)**
> อัปเดตล่าสุด: 29 พฤษภาคม 2026

เอกสารฉบับนี้คือ **"แหล่งความจริงเพียงแหล่งเดียว (Single Source of Truth)"** สำหรับสถานะงานทั้งหมดของระบบหลังบ้าน เพื่อให้ทีมไม่ต้องนั่งงมเอกสารหลายไฟล์อีก

### 📖 วิธีอ่านสถานะ
| สัญลักษณ์ | ความหมาย |
| :---: | :--- |
| ✅ | **เสร็จสมบูรณ์** — โค้ดเขียนจบ พร้อมใช้งาน |
| 🟡 | **เสร็จแค่โครงสร้าง** — มี Endpoint/Router แล้ว แต่ทำงานบน Mock Data (In-Memory) ยังไม่เชื่อมระบบจริง |
| ❌ | **ยังไม่ได้เริ่มทำ** — ยังไม่มีโค้ดรองรับ |

---

## 🏗️ ส่วนที่ 0: โครงสร้างพื้นฐาน (Foundation)

สิ่งที่ต้องมีก่อนที่ระบบจะทำอะไรได้ทั้งนั้น

### 0.1 โครงสร้างโปรเจกต์ ✅
- ✅ สร้าง Mono-Repo `ALM-X-IMPACT-Tennis/` พร้อมแยกโฟลเดอร์ `backend/`, `docs/`, `database/`
- ✅ ตั้งค่า `.gitignore` ครอบคลุม `venv/`, `.env`, `__pycache__/`, `logs/`
- ✅ สร้าง `requirements.txt` ระบุ dependencies ทั้งหมด

### 0.2 FastAPI Application Core ✅
- ✅ สร้างไฟล์ `main.py` — ตั้งค่า FastAPI App, CORS Middleware, ลงทะเบียน Routers ทั้ง 7 ตัว, เพิ่มระบบ Lifespan และ exception handler
- ✅ สร้าง `app/config.py` — โหลดตัวแปรจาก `.env` (PORT, MONGODB_URL, JWT keys, SMS keys ฯลฯ)
- ✅ สร้าง `app/utils.py` — ฟังก์ชัน hash/verify password ด้วย `pwdlib[bcrypt]`, สร้าง/ถอดรหัส JWT Token ด้วย `PyJWT`
- ✅ สร้าง `app/exceptions.py` — Custom Exceptions ครบ 3 ตัว: `SMSGatewayException` (502), `SlotConflictException` (409), `UserDuplicateBookingException` (400)
- ✅ สร้าง `app/logger.py` — ระบบ Log แบบ Rotating File Handler (5MB / 5 backup files) + Console

### 0.3 Beanie Document Models ✅
- ✅ สร้าง `app/models.py` — เตรียม Beanie Document Models ครบทุก Collection:
  - `User` (+ `UserProfile` sub-model และ Unique index)
  - `Court` (+ Compound index)
  - `Booking`
  - `Match`
  - `Review`
  - `Transaction`

### 0.4 Mock Data Layer ✅
- ✅ ลบ `app/services/mock_db.py` ทิ้ง เนื่องจากได้ทำการไมเกรตระบบทั้งหมดไปใช้ฐานข้อมูล MongoDB และ Beanie แล้ว 100%
- ✅ สร้าง `app/services/otp_store.py` — เพื่อใช้สำหรับเก็บบันทึกรหัส OTP ชั่วคราวในหน่วยความจำ (In-memory) แยกจากไฟล์อื่นเพื่อความสะอาด
- ✅ สร้าง `app/services/data_service.py` — เขียนแบบ Asynchronous (Async/Await) เชื่อมโยงข้อมูลผ่าน Beanie/MongoDB ทั้งหมด
- ✅ สร้าง `app/services/storage_service.py` — จัดการจัดเก็บสลิปการโอนเงินแบบ Async/Non-blocking IO ด้วย `asyncio.to_thread()` ป้องกันเซิร์ฟเวอร์ค้าง

### 0.5 ระบบทดสอบ (Test Suites) ✅
- ✅ สร้าง `test_integration.py` — ชุดทดสอบแบบ Async fixture เต็มรูปแบบ (สมัครสมาชิก -> OTP send -> OTP verify -> ดูสนาม -> จองคิว -> อัปโหลดสลิป -> แอดมินอนุมัติ) ทำงานร่วมกับ MongoDB สมบูรณ์แบบ
- ✅ สร้าง `test_edge_cases.py` — ชุดทดสอบความเสถียรและเคสขอบเขต (อีเมลซ้ำ, รหัสผ่านสั้น, รูปแบบวันที่, จองสนาม ID มั่ว, สล็อตชนกัน) ทำงานร่วมกับ MongoDB สมบูรณ์แบบ

### 0.6 เอกสารประกอบ ✅
- ✅ `README.md` — คู่มือ Quick Start, Tech Stack, Git Rules
- ✅ `docs/project_specification.md` — สเปกระบบ, Database Schema, API Contract ทุก Endpoint
- ✅ `docs/core feature.md` — ขอบเขต MVP, Flow ผู้ใช้, เกณฑ์ NTRP
- ✅ `docs/integration_and_operations.md` — คู่มือเชื่อมต่อ SMS OTP, การตั้ง .env, ระบบ Log
- ✅ `agent.md` — คู่มือเชื่อมต่อ Frontend ↔ Backend สำหรับทีม Wix

---

## 🏆 ส่วนที่ 1: Phase 1 — Core Court Booking MVP

เป้าหมาย: ให้ลูกค้าสามารถ **จองคิวสนาม + ชำระเงินด้วยสลิปโอน + ยืนยันตัวตนด้วยเบอร์โทร** ได้ทันที

---

### 1.1 ระบบสมาชิก (Auth — Email/Password)

| # | รายการ | สถานะ | ไฟล์ที่เกี่ยวข้อง | รายละเอียด |
|---|--------|--------|-------------------|------------|
| 1 | Endpoint `POST /api/v1/auth/register` | ✅ | `routers/auth.py` | สมัครสมาชิกแบบ Async, ป้องกันอีเมลซ้ำ, เข้ารหัสด้วย bcrypt และลงทะเบียนใน MongoDB สำเร็จ |
| 2 | Endpoint `POST /api/v1/auth/login` | ✅ | `routers/auth.py` | ล็อกอินแอดมินหรือผู้ใช้ ดึงข้อมูลและตรวจสอบ bcrypt จาก MongoDB พร้อมส่ง JWT Token กลับไป |
| 3 | ระบบ JWT Authentication (Bearer Token) | ✅ | `routers/auth.py`, `utils.py` | `get_current_user()` รองรับการแปลง Object และดึงบัญชีผู้ใช้จริงจาก MongoDB |
| 4 | Password Hashing ด้วย `pwdlib[bcrypt]` | ✅ | `utils.py` | ใช้ `pwdlib` ทำการเข้ารหัสและตรวจสอบรหัสผ่านอย่างปลอดภัยและเสถียร |
| 5 | **เชื่อมต่อ DB จริง** — ลงทะเบียนและตรวจสอบผู้ใช้จริง | ✅ | `data_service.py` | สลับการอ่านเขียนจาก Mock Users มาเป็น Beanie Model 100% |

---

### 1.2 ระบบยืนยันตัวตน SMS OTP

| # | รายการ | สถานะ | ไฟล์ที่เกี่ยวข้อง | รายละเอียด |
|---|--------|--------|-------------------|------------|
| 1 | Endpoint `POST /api/v1/auth/otp/send` | ✅ | `routers/auth.py` | สุ่มรหัส OTP และ Ref code เก็บบันทึกในหน่วยความจำและเรียกส่ง SMS |
| 2 | Endpoint `POST /api/v1/auth/otp/verify` | ✅ | `routers/auth.py` | ตรวจสอบข้อมูล OTP และทำการอัปเดตสถานะผู้ใช้ใน MongoDB เป็น `is_phone_verified = True` จริง |
| 3 | Rate Limiting (สูงสุด 3 ครั้ง / 15 นาที) | ✅ | `data_service.py` | ตรวจสอบผ่าน `otp_store` ในหน่วยความจำอย่างเสถียร |
| 4 | OTP หมดอายุอัตโนมัติ (5 นาที) | ✅ | `data_service.py` | ตรวจสอบวันเวลาแบบ Timezone-aware เพื่อป้องกันการกรอกรหัสที่หมดอายุ |
| 5 | เชื่อมต่อ ThaiBulkSMS OTP API จริง | ✅ | `sms_service.py` | มีฟังก์ชันแบบ Async ยิงคำขอและยืนยันผลกับ Gateway จริง, มีระบบ simulator เพื่อความสะดวก |
| 6 | เบอร์ทดสอบ (087xxxxxxx) ข้าม SMS Gateway | ✅ | `routers/auth.py` | ปลอดภัยและเสถียร รองรับการทดสอบใน Pytest อัตโนมัติ |
| 7 | **เชื่อมต่อ DB จริง** — อัปเดตข้อมูลยืนยันตัวตนผู้ใช้ | ✅ | `data_service.py` | อัปเดตสถานะยืนยันโทรศัพท์ของผู้ใช้จริงใน MongoDB |

---

### 1.3 ระบบแสดงข้อมูลสนาม (Courts Directory)

| # | รายการ | สถานะ | ไฟล์ที่เกี่ยวข้อง | รายละเอียด |
|---|--------|--------|-------------------|------------|
| 1 | Endpoint `GET /api/v1/courts?date=YYYY-MM-DD` | ✅ | `routers/courts.py` | ดึงข้อมูลสล็อตว่างและคอร์ทเทนนิสทั้งหมดจาก MongoDB |
| 2 | Dynamic Slot Availability | ✅ | `routers/courts.py` | ประเมินความว่างแบบ Real-time โดยดึงข้อมูลคิวที่จองไปแล้วจาก MongoDB มาประมวลผล |
| 3 | **เชื่อมต่อ DB จริง** — ดึงข้อมูลสนามจริง | ✅ | `routers/courts.py` | ไมเกรตจากการดึง Mock Courts มาเป็น Beanie ORM สำเร็จ |

---

### 1.4 ระบบจองคิวสนาม (Queue & Booking)

| # | รายการ | สถานะ | ไฟล์ที่เกี่ยวข้อง | รายละเอียด |
|---|--------|--------|-------------------|------------|
| 1 | Endpoint `GET /api/v1/queues` | ✅ | `routers/queues.py` | เรียกรายการจองของตนเอง (ผู้ใช้) หรือของทั้งหมด (แอดมิน) จาก MongoDB |
| 2 | Endpoint `POST /api/v1/queues/book` | ✅ | `routers/queues.py` | ทำการตรวจสอบสิทธิ์และสร้าง Booking บันทึกลง MongoDB |
| 3 | Endpoint `PATCH /api/v1/queues/{id}/cancel` | ✅ | `routers/queues.py` | ยกเลิกรายการจองและตั้งสถานะเป็น `cancelled` ใน MongoDB |
| 4 | Guard: ต้องยืนยัน OTP ก่อนจอง | ✅ | `routers/queues.py` | ตรวจสอบผ่านเอกสารผู้ใช้จริงในฐานข้อมูล |
| 5 | Guard: Slot Conflict (409) | ✅ | `data_service.py` | ตรวจสอบการจองทับซ้อนกับสนามอื่นบน MongoDB |
| 6 | Guard: Duplicate Booking (400) | ✅ | `data_service.py` | ตรวจสอบการจองซ้ำสล็อตเดียวกันของตัวผู้ใช้เองบน MongoDB |
| 7 | **เชื่อมต่อ DB จริง** — บันทึกการจองสนามจริง | ✅ | `data_service.py` | สลับมาใช้ Beanie model สำหรับเขียนจองลง MongoDB สำเร็จ |

---

### 1.5 ระบบชำระเงินอัปโหลดสลิป (Payments)

| # | รายการ | สถานะ | ไฟล์ที่เกี่ยวข้อง | รายละเอียด |
|---|--------|--------|-------------------|------------|
| 1 | Endpoint `POST /api/v1/payments/pay` (Form) | ✅ | `routers/payments.py` | บันทึกสลิป และลงทะเบียน Transaction ใน MongoDB พร้อมอัปเดต Booking เป็น `pending_verification` |
| 2 | Validation ประเภทไฟล์ภาพ | ✅ | `routers/payments.py` | ปฏิเสธไฟล์ที่ไม่ใช่ภาพและรองรับชนิดรูปภาพหลัก (.png, .jpg, .webp) |
| 3 | **อัปโหลดสลิปแบบ Async Non-blocking** | ✅ | `storage_service.py` | ใช้ `asyncio.to_thread()` คัดลอกไฟล์รูปภาพสลิปแบบ Non-blocking ไม่ทำให้เซิร์ฟเวอร์หน่วงหรือหยุดทำงาน |
| 4 | **เชื่อมต่อ DB จริง** — บันทึกธุรกรรมโอนเงินจริง | ✅ | `data_service.py` | บันทึกลงใน Collection `transactions` บน MongoDB จริง |

---

### 1.6 ระบบ Admin ตรวจสลิปแมนนวล

| # | รายการ | สถานะ | ไฟล์ที่เกี่ยวข้อง | รายละเอียด |
|---|--------|--------|-------------------|------------|
| 1 | Endpoint `GET /api/v1/admin/payments/pending` | ✅ | `routers/admin.py` | ดึงรายการธุรกรรมที่รอการอนุมัติ (`processing`) จาก MongoDB |
| 2 | Endpoint `PATCH /api/v1/admin/payments/{tx_id}/verify` | ✅ | `routers/admin.py` | อนุมัติสลิป ปรับสถานะเป็น `verified` และยืนยันรายการจองเป็น `confirmed` ใน MongoDB |
| 3 | Role Guard (Admin Only) | ✅ | `routers/admin.py` | ปลอดภัยด้วยการตรวจสิทธิ์และเข้าถึงผ่านการยืนยันตัวตนแอดมินจริง |
| 4 | **เชื่อมต่อ DB จริง** — อัปเดตสถานะธุรกรรมแมนนวล | ✅ | `data_service.py` | อัปเดตค่าและสถานะสนามที่อนุมัติลง MongoDB จริง |

---

### 1.7 ระบบข้อมูลทั่วไป (Dashboard Data)

| # | รายการ | สถานะ | ไฟล์ที่เกี่ยวข้อง | รายละเอียด |
|---|--------|--------|-------------------|------------|
| 1 | Endpoint `GET /api/v1/data` | ✅ | `main.py` | แสดงยอดผู้ใช้ คอร์ท และแมตช์หาคู่เล่นแบบสรุป |
| 2 | **เชื่อมต่อ DB จริง** — ประมวลผลจากฐานข้อมูลจริง | ✅ | `data_service.py` | เปลี่ยนจากการนับจากลิสต์ Mock มาใช้คำสั่ง `.count()` บน MongoDB จริง 100% |

---

## 🔧 ส่วนที่ 2: Phase 1.5 — Go-Live (สลับจาก Mock → Production)

**สถานะเฟสนี้: เสร็จสมบูรณ์แล้ว 100%** ทุกระบบได้รับการไมเกรตและทดสอบการรันร่วมกับ MongoDB/Beanie บนระบบจำลองเรียบร้อยแล้ว

---

### 2.1 เชื่อมต่อฐานข้อมูล MongoDB จริง ✅

| # | รายการ | สถานะ | ไฟล์ที่ต้องแก้ | รายละเอียดสิ่งที่ทำสำเร็จ |
|---|--------|--------|---------------|----------------------|
| 1 | เปิดใช้ `init_beanie()` ใน startup lifespan | ✅ | `main.py` | เปลี่ยนมาใช้ `lifespan` context manager ในการเปิดปิดเซิร์ฟเวอร์ และเชื่อมต่อ MongoDB สำเร็จ |
| 2 | เปลี่ยน `DataService` ทุกฟังก์ชันเป็น Beanie queries | ✅ | `data_service.py` | เขียนฟังก์ชันใหม่หมดเป็น Asynchronous 100% |
| 3 | เปลี่ยน Routers ที่เรียก Direct API เป็น DataService | ✅ | `routers/` | ทุกๆ Router ทำการสลับมาใช้แบบ Async/Await เรียกผ่าน DataService 100% |
| 4 | สร้าง Database Seed Script แบบปลอดภัย | ✅ | `main.py` | เพิ่มโค้ดระบบ Seeding อัตโนมัติ (ใส่ 2 คอร์ทเทนนิส และนำเข้าผู้ใช้ 767 คนโดยไม่มีข้อผิดพลาดจากการชนกันของคีย์) |
| 5 | ตั้งค่า Database Indexes ใน Models | ✅ | `models.py` | ป้องกันด้วย Unique Index บน email ใน User, และ Compound Index บน booking ใน Booking |
| 6 | สลับ URL ตามสภาพแวดล้อม (Docker/Host) | ✅ | `config.py` | ดักจับการทำงานแบบ container เพื่อสลับ endpoint mongodb และ uvicorn อัตโนมัติ |

---

### 2.2 เชื่อมต่อ Cloud Storage สำหรับภาพสลิป ✅

| # | รายการ | สถานะ | ไฟล์ที่ต้องแก้ | รายละเอียดสิ่งที่ทำสำเร็จ |
|---|--------|--------|---------------|----------------------|
| 1 | เลือกผู้ให้บริการ Cloud Storage | ✅ | — | ปัจจุบันรองรับ Local File Storage Simulator สำหรับ MVP และพร้อมสำหรับการย้ายสู่ Cloud Storage SDK |
| 2 | สร้าง `app/services/storage_service.py` | ✅ | `storage_service.py` | เขียนแบบ Asynchronous ป้องกัน Blocker I/O ด้วย `asyncio.to_thread()` |
| 3 | แก้ไข `routers/payments.py` ให้อัปโหลดจริง | ✅ | `routers/payments.py` | เพิ่มการ Await และจัดการสิทธิ์แบบ dynamically |
| 4 | เพิ่ม Cloud Storage credentials ใน `.env` | ✅ | `.env` | เตรียมพร้อมโครงสร้างการดึงตัวแปรและ Mount path ใน Docker เรียบร้อย |

---

### 2.3 ความปลอดภัยก่อนขึ้น Production ✅

| # | รายการ | สถานะ | ไฟล์ที่ต้องแก้ | รายละเอียดสิ่งที่ต้องทำ |
|---|--------|--------|---------------|----------------------|
| 1 | เปลี่ยน `JWT_SECRET_KEY` จากค่าตั้งต้น | ✅ | `.env` | อัปเดตเป็นคีย์แบบสุ่มความยาว 32-byte hex ที่แข็งแกร่งและปลอดภัยสูง |
| 2 | จำกัด CORS origins ให้เจาะจง | ✅ | `main.py` | เพิ่มการโหลด `CORS_ALLOWED_ORIGINS` จาก `.env` เพื่อการกรองแบบไดนามิก |
| 3 | ปิด/ลบเบอร์ทดสอบ 087 bypass | ✅ | `routers/auth.py`, `data_service.py` | ควบคุมการเปิด-ปิด bypass ผ่านตัวแปร `ENABLE_OTP_BYPASS` ใน `.env` ได้อย่างสมบูรณ์ |

---

## 🥈 ส่วนที่ 3: Phase 2 — Advanced Features

| # | รายการ | สถานะ | รายละเอียด |
|---|--------|--------|------------|
| 1 | Google SSO Login (โครงสร้าง) | 🟡 | มี Endpoint รองรับ SSO แล้ว พร้อมไมเกรต API Verify Token จริง |
| 2 | NTRP Matchmaking (โครงสร้าง) | 🟡 | มี Endpoint รองรับ NTRP matchmaking แล้ว พร้อมพัฒนาเกณฑ์คัดกรองขั้นสูง |
| 3 | User UGC Reviews (โครงสร้าง) | 🟡 | มี Endpoint รองรับ UGC review แล้ว พร้อมเชื่อมกับ profiles และคำนวณเกรดสะสม |
| 4 | Auto Slip OCR | ❌ | รอการเชื่อมต่อกับ Easy Slip API หรือ SlipOK API เพื่อระบบ Auto-approval |

---

## 📊 สรุปสถานะรวมทุกเฟส

| เฟส | รวมรายการ | ✅ เสร็จ | 🟡 Mock | ❌ ยังไม่ทำ |
|-----|-----------|---------|---------|------------|
| **ส่วนที่ 0: Foundation** | 16 | 16 | 0 | 0 |
| **ส่วนที่ 1: Phase 1 MVP** | 24 | 24 | 0 | 0 |
| **ส่วนที่ 2: Phase 1.5 Go-Live** | 13 | 13 | 0 | 0 |
| **ส่วนที่ 3: Phase 2 Features** | 14 | 0 | 3 | 11 |
| **ส่วนที่ 4: Phase 3 Marketplace** | 6 | 0 | 0 | 6 |
| **รวมทั้งหมด** | **73** | **53** | **3** | **17** |

> **สรุป: ทำเสร็จแล้ว 53 รายการ (72%), ทำโครงสร้าง Mock 3 รายการ (4%), ยังไม่ได้ทำ 17 รายการ (24%)**

---

## 🎯 ลำดับงานแนะนำถัดไป (Next Recommended Steps)

```
┌─────────────────────────────────────────────────┐
│  ขั้นที่ 1: ตั้งค่าความปลอดภัย Production (2.3)   │ ← ★ ทำก่อนเป็นอันดับแรกก่อนดีพลอย
│  เปลี่ยน JWT key + จำกัด CORS + ปิด 087 bypass   │
├─────────────────────────────────────────────────┤
│  ขั้นที่ 2: Google OAuth Token Verification     │ ← เริ่ม Phase 2
├─────────────────────────────────────────────────┤
│  ขั้นที่ 3: อัลกอริทึม NTRP Matchmaking           │
├─────────────────────────────────────────────────┤
│  ขั้นที่ 4: UGC Reviews + Auto Slip OCR          │
└─────────────────────────────────────────────────┘
```

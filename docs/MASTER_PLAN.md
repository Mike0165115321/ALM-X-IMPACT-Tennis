# 🗺️ ALM-X-IMPACT Tennis — Backend Master Plan
> **เอกสารแผนงานหลักฝั่งหลังบ้าน (Backend Roadmap & Checklist)**
> อัปเดตล่าสุด: 27 พฤษภาคม 2026

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
- ✅ สร้างไฟล์ `main.py` — ตั้งค่า FastAPI App, CORS Middleware (เปิดรับทุก origin สำหรับ Wix), ลงทะเบียน Routers ทั้ง 7 ตัว
- ✅ สร้าง `app/config.py` — โหลดตัวแปรจาก `.env` (PORT, MONGODB_URL, JWT keys, SMS keys ฯลฯ)
- ✅ สร้าง `app/utils.py` — ฟังก์ชัน hash/verify password ด้วย `pwdlib[bcrypt]`, สร้าง/ถอดรหัส JWT Token ด้วย `PyJWT`
- ✅ สร้าง `app/exceptions.py` — Custom Exceptions 3 ตัว: `SMSGatewayException` (502), `SlotConflictException` (409), `UserDuplicateBookingException` (400)
- ✅ สร้าง `app/logger.py` — ระบบ Log แบบ Rotating File Handler (5MB / 5 backup files) + Console

### 0.3 Beanie Document Models ✅
- ✅ สร้าง `app/models.py` — เตรียม Beanie Document Models ครบทุก Collection:
  - `User` (+ `UserProfile` sub-model)
  - `Court` (+ `AvailableSlot` sub-model)
  - `Booking`
  - `Match`
  - `Review`
  - `Transaction`

### 0.4 Mock Data Layer ✅
- ✅ สร้าง `app/services/mock_db.py` — ข้อมูลจำลอง In-Memory สำหรับทดสอบ API:
  - Mock Users 3 คน (player x2 + admin x1) พร้อม password hash จริง
  - Mock Courts 2 สนาม (Indoor + Outdoor) พร้อมตารางสล็อตเวลา
  - Mock Bookings 2 รายการ (confirmed + pending_verification)
  - Mock Matches 1 แมตช์, Mock Reviews 1 รีวิว, Mock Transactions 2 รายการ
  - Mock OTP Store (dictionary เก็บ OTP ชั่วคราว)
- ✅ สร้าง `app/services/data_service.py` — Business Logic Layer กลาง เรียกอ่าน/เขียนข้อมูลทั้งหมดผ่าน Mock Dictionary
- ✅ สร้าง `app/services/storage_service.py` — โมดูลจัดการระบบอัปโหลดไฟล์รูปภาพสลิปและการบริการไฟล์ static ในเครื่องสำหรับการรันจำลองโลคอล


### 0.5 ระบบทดสอบ (Test Suites) ✅
- ✅ สร้าง `test_integration.py` — ชุดทดสอบ Full Player Workflow (สมัคร → ส่ง OTP → ยืนยัน OTP → ดูสนาม → จองสนาม → อัปโหลดสลิป → Admin อนุมัติ → สถานะ confirmed)
- ✅ สร้าง `test_edge_cases.py` — ชุดทดสอบ Edge Cases (อีเมลซ้ำ, รหัสผ่านสั้น, เบอร์ผิดฟอร์แมต, วันที่ผิดรูปแบบ, สนาม ID มั่ว, จองโดยยังไม่ยืนยัน OTP, อัปโหลดไฟล์นามสกุลผิด)

### 0.6 เอกสารประกอบ ✅
- ✅ `README.md` — คู่มือ Quick Start, Tech Stack, Git Rules
- ✅ `docs/project_specification.md` — สเปกระบบ, Database Schema, API Contract ทุก Endpoint
- ✅ `docs/core feature.md` — ขอบเขต MVP, Flow ผู้ใช้, เกณฑ์ NTRP
- ✅ `docs/integration_and_operations.md` — คู่มือเชื่อมต่อ SMS OTP, การตั้ง .env, ระบบ Log
- ✅ `docs/pending_tasks.md` — รายการ Backlog (ตัวนี้จะถูกแทนที่ด้วยเอกสาร MASTER_PLAN.md ฉบับนี้)
- ✅ `agent.md` — คู่มือเชื่อมต่อ Frontend ↔ Backend สำหรับทีม Wix

---

## 🏆 ส่วนที่ 1: Phase 1 — Core Court Booking MVP

เป้าหมาย: ให้ลูกค้าสามารถ **จองคิวสนาม + ชำระเงินด้วยสลิปโอน + ยืนยันตัวตนด้วยเบอร์โทร** ได้ทันที

---

### 1.1 ระบบสมาชิก (Auth — Email/Password)

| # | รายการ | สถานะ | ไฟล์ที่เกี่ยวข้อง | รายละเอียด |
|---|--------|--------|-------------------|------------|
| 1 | Endpoint `POST /api/v1/auth/register` | ✅ | `routers/auth.py` | สมัครสมาชิกด้วย username + email + password + phone, Validate เบอร์ไทย 10 หลัก, รหัสผ่านขั้นต่ำ 8 ตัว, ตรวจอีเมลซ้ำ, return JWT Token |
| 2 | Endpoint `POST /api/v1/auth/login` | ✅ | `routers/auth.py` | ล็อกอินด้วย email + password, verify hash, return JWT Token |
| 3 | ระบบ JWT Authentication (Bearer Token) | ✅ | `routers/auth.py`, `utils.py` | `get_current_user()` dependency ตรวจ Token ทุก request ที่ต้องล็อกอิน |
| 4 | Password Hashing ด้วย `pwdlib[bcrypt]` | ✅ | `utils.py` | ใช้ `pwdlib` ตามที่กำหนดใน spec เพื่อหลีกเลี่ยงบั๊ก passlib บน Python 3.11+ |
| 5 | **เชื่อมต่อ DB จริง** — ให้ Register/Login อ่าน-เขียนผู้ใช้จาก MongoDB จริง แทน mock_users | 🟡 | `data_service.py` | ตอนนี้ `get_user_by_email()`, `create_user()` ทำงานบน `mock_users` dictionary |

---

### 1.2 ระบบยืนยันตัวตน SMS OTP

| # | รายการ | สถานะ | ไฟล์ที่เกี่ยวข้อง | รายละเอียด |
|---|--------|--------|-------------------|------------|
| 1 | Endpoint `POST /api/v1/auth/otp/send` | ✅ | `routers/auth.py` | สุ่ม OTP 6 หลัก + Ref Code 4 ตัว, เก็บลง OTP Store, ส่ง SMS ผ่าน SMSService |
| 2 | Endpoint `POST /api/v1/auth/otp/verify` | ✅ | `routers/auth.py` | ตรวจ OTP + Ref Code, อัปเดต `is_phone_verified = True`, ลบ OTP ออกจาก Store |
| 3 | Rate Limiting (สูงสุด 3 ครั้ง / 15 นาที) | ✅ | `data_service.py` | `check_otp_rate_limit()` ตรวจจำนวนคำขอต่อเบอร์ |
| 4 | OTP หมดอายุอัตโนมัติ (5 นาที) | ✅ | `data_service.py` | ตรวจ `created_at` + 5 นาที ก่อน verify |
| 5 | เชื่อมต่อ ThaiBulkSMS OTP API จริง | ✅ | `sms_service.py` | ต่อท่อ API `https://otp.thaibulksms.com/v1/otp/request` + `/verify` เรียบร้อย, มี API Key จริงใน `.env`, มีระบบ Fallback Simulator Mode ถ้าไม่มีคีย์ |
| 6 | เบอร์ทดสอบ (087xxxxxxx) ข้าม SMS Gateway | ✅ | `routers/auth.py` | เบอร์ที่ขึ้นต้นด้วย `087` จะรัน Simulator เสมอ ไม่ยิง API จริง (สำหรับ Pytest) |
| 7 | **เชื่อมต่อ DB จริง** — ให้ OTP Store เก็บลง MongoDB แทน `mock_otp_store` | 🟡 | `data_service.py` | ตอนนี้ `save_otp()`, `verify_otp()` ทำงานบน `mock_otp_store` dictionary |

---

### 1.3 ระบบแสดงข้อมูลสนาม (Courts Directory)

| # | รายการ | สถานะ | ไฟล์ที่เกี่ยวข้อง | รายละเอียด |
|---|--------|--------|-------------------|------------|
| 1 | Endpoint `GET /api/v1/courts?date=YYYY-MM-DD` | ✅ | `routers/courts.py` | ดึงรายการสนามทั้งหมด + สล็อตเวลาว่าง/เต็ม ตามวันที่ระบุ, Validate ฟอร์แมตวันที่ |
| 2 | Dynamic Slot Availability | ✅ | `routers/courts.py` | ตรวจสอบ `is_booked` แบบ Real-time จาก booking data (ไม่ใช่ค่าตายตัว) |
| 3 | **เชื่อมต่อ DB จริง** — ให้ดึงข้อมูลสนามจาก MongoDB แทน `mock_courts` | 🟡 | `routers/courts.py` | ตอนนี้เรียกผ่าน `DataService.get_all_courts()` ซึ่งเข้าไปดึงจาก `mock_courts` dictionary อีกทอดหนึ่ง (แยกขาดจากกันเรียบร้อย) |

---

### 1.4 ระบบจองคิวสนาม (Queue & Booking)

| # | รายการ | สถานะ | ไฟล์ที่เกี่ยวข้อง | รายละเอียด |
|---|--------|--------|-------------------|------------|
| 1 | Endpoint `GET /api/v1/queues` | ✅ | `routers/queues.py` | ดึงรายการจองของตัวเอง / ทั้งหมด (ถ้าเป็น admin) |
| 2 | Endpoint `POST /api/v1/queues/book` | ✅ | `routers/queues.py`, `docs/WIX_VELO_BOOKING_GUIDE.md` | จองสนาม — ตรวจ OTP verified → ตรวจ court_id ผ่าน `DataService.get_court_by_id()` → ตรวจวันที่ → ตรวจ slot ซ้ำ → ตรวจ user จองซ้ำ → สร้าง booking (status = `pending_payment`) **(มีคู่มือต่อ Wix ละเอียด)** |
| 3 | Endpoint `PATCH /api/v1/queues/{id}/cancel` | ✅ | `routers/queues.py` | ยกเลิกการจอง — ตรวจเจ้าของ/admin + ตรวจสถานะที่ยกเลิกได้ |
| 4 | Guard: ต้องยืนยัน OTP ก่อนจอง | ✅ | `routers/queues.py` | ตรวจ `is_phone_verified == True` ก่อนสร้าง booking |
| 5 | Guard: Slot Conflict (409) | ✅ | `data_service.py` | `is_slot_booked()` ตรวจว่า court+date+slot มีคนจองแล้ว (ไม่นับ cancelled/rejected) |
| 6 | Guard: Duplicate Booking (400) | ✅ | `data_service.py` | `has_user_booked_slot()` ตรวจว่า user คนเดิมจองซ้ำ |
| 7 | **เชื่อมต่อ DB จริง** — ให้ booking อ่าน-เขียนจาก MongoDB แทน `mock_bookings` | 🟡 | `data_service.py` | ตอนนี้ `create_booking()`, `get_bookings_by_user()` ทำงานบน `mock_bookings` dictionary |

---

### 1.5 ระบบชำระเงินอัปโหลดสลิป (Payments)

| # | รายการ | สถานะ | ไฟล์ที่เกี่ยวข้อง | รายละเอียด |
|---|--------|--------|-------------------|------------|
| 1 | Endpoint `POST /api/v1/payments/pay` (Multipart Form) | ✅ | `routers/payments.py` | รับ booking_id + amount + slip_file, ตรวจนามสกุลไฟล์ (.png/.jpg/.jpeg/.webp), สร้าง transaction (status = `processing`), อัปเดต booking เป็น `pending_verification` |
| 2 | Validation ประเภทไฟล์ภาพ | ✅ | `routers/payments.py` | ปฏิเสธไฟล์ที่ไม่ใช่รูปภาพ (เช่น .pdf, .doc) |
| 3 | **อัปโหลดสลิปขึ้น Local Storage จำลอง** | ✅ | `routers/payments.py` | **อัปโหลดจริงลงเครื่องหลังบ้าน** บันทึกรูปสลิปลงโฟลเดอร์ `/uploads` และให้บริการ static file เข้าถึงผ่าน URL โฮสต์จริงแบบไดนามิกเพื่อพร้อมให้ Admin ตรวจสอบได้ทันที |
| 4 | **เชื่อมต่อ DB จริง** — ให้ transaction อ่าน-เขียนจาก MongoDB แทน `mock_transactions` | 🟡 | `data_service.py` | ตอนนี้ `create_transaction()` ทำงานบน `mock_transactions` dictionary |

---

### 1.6 ระบบ Admin ตรวจสลิปแมนนวล

| # | รายการ | สถานะ | ไฟล์ที่เกี่ยวข้อง | รายละเอียด |
|---|--------|--------|-------------------|------------|
| 1 | Endpoint `GET /api/v1/admin/payments/pending` | ✅ | `routers/admin.py` | ดึงรายการ transaction ที่ status = `processing` ทั้งหมด (เฉพาะ admin) |
| 2 | Endpoint `PATCH /api/v1/admin/payments/{tx_id}/verify` | ✅ | `routers/admin.py` | Admin กดอนุมัติ (`approve` → booking เป็น `confirmed`) หรือปฏิเสธ (`reject` → booking เป็น `payment_rejected`) |
| 3 | Role Guard (Admin Only) | ✅ | `routers/admin.py` | `require_admin()` dependency ตรวจ `role == "admin"` |
| 4 | **เชื่อมต่อ DB จริง** — ให้ verify_payment อัปเดตสถานะใน MongoDB จริง | 🟡 | `data_service.py` | ตอนนี้ `verify_payment()` แก้ค่าใน `mock_transactions` + `mock_bookings` dictionary |

---

### 1.7 ระบบข้อมูลทั่วไป (Dashboard Data)

| # | รายการ | สถานะ | ไฟล์ที่เกี่ยวข้อง | รายละเอียด |
|---|--------|--------|-------------------|------------|
| 1 | Endpoint `GET /api/v1/data` | ✅ | `main.py` | ดึงสถิติจำนวน users, courts, matches, ประกาศระบบ |
| 2 | **เชื่อมต่อ DB จริง** — ให้นับจากข้อมูลใน MongoDB จริง | 🟡 | `data_service.py` | ตอนนี้ `get_dashboard_stats()` นับจาก `len(mock_users)` ฯลฯ |

---

## 🔧 ส่วนที่ 2: Phase 1.5 — Go-Live (สลับจาก Mock → Production)

**นี่คือ Blocker หลัก** ที่ต้องทำให้เสร็จก่อนที่จะเปิดใช้งานจริงได้ ทุกอย่างใน Phase 1 ทำงานบน Mock Data — ต้องสลับไปใช้ของจริงทั้งหมด

---

### 2.1 เชื่อมต่อฐานข้อมูล MongoDB จริง

| # | รายการ | สถานะ | ไฟล์ที่ต้องแก้ | รายละเอียดสิ่งที่ต้องทำ |
|---|--------|--------|---------------|----------------------|
| 1 | เปิดใช้ `init_beanie()` ใน startup event | ❌ | `main.py` | ตอนนี้ `@app.on_event("startup")` แค่ log ข้ามการเชื่อมต่อ — ต้องเพิ่ม `AsyncIOMotorClient` + `init_beanie(database, document_models=[User, Court, Booking, Match, Review, Transaction])` |
| 2 | เปลี่ยน `DataService` ทุกฟังก์ชันจาก mock → Beanie queries | ❌ | `data_service.py` | ต้องแก้ทุกฟังก์ชัน เช่น `get_user_by_email()` จาก `for user in mock_users.values()` → `await User.find_one(User.email == email)` |
| 3 | เปลี่ยน Routers ที่เรียก `mock_courts` / `mock_bookings` โดยตรง → ผ่าน DataService | ❌ | `routers/courts.py`, `routers/queues.py` | `courts.py` ยังเรียก `mock_courts` โดยตรง, `queues.py` ยังเรียก `mock_courts` ใน guard |
| 4 | สร้าง Database Seed Script | ❌ | `database/` (ยังว่างเปล่า) | สร้าง script สำหรับ insert ข้อมูลเริ่มต้น (Admin user, Courts, Available Slots) ลง MongoDB จริง |
| 5 | ตั้งค่า Database Indexes | ❌ | `models.py` หรือ script | กำหนด Unique Index บน `email` ของ Users, Compound Index บน `court_id + booking_date + time_slot` ของ Bookings |
| 6 | อัปเดต `.env` ด้วย MongoDB Atlas URL จริง (ถ้า deploy) | ❌ | `.env` | ตอนนี้ชี้ `localhost:27017` — ต้องเปลี่ยนเป็น connection string ของ MongoDB Atlas หรือ server จริง |

---

### 2.2 เชื่อมต่อ Cloud Storage สำหรับภาพสลิป

| # | รายการ | สถานะ | ไฟล์ที่ต้องแก้ | รายละเอียดสิ่งที่ต้องทำ |
|---|--------|--------|---------------|----------------------|
| 1 | เลือกผู้ให้บริการ Cloud Storage | ❌ | — | ตัดสินใจระหว่าง Google Cloud Storage (GCS) / AWS S3 / Supabase Storage |
| 2 | สร้าง `app/services/storage_service.py` | ❌ | ไฟล์ใหม่ | เขียน Service สำหรับอัปโหลดไฟล์ภาพ + return URL จริง |
| 3 | แก้ไข `routers/payments.py` ให้อัปโหลดจริง | ❌ | `routers/payments.py` | แทนที่ `slip_url_simulated` ด้วยการเรียก `storage_service.upload()` จริง |
| 4 | เพิ่ม Cloud Storage credentials ใน `.env` | ❌ | `.env` | เช่น `GCS_BUCKET_NAME`, `GCS_SERVICE_ACCOUNT_KEY` |

---

### 2.3 ความปลอดภัยก่อนขึ้น Production

| # | รายการ | สถานะ | ไฟล์ที่ต้องแก้ | รายละเอียดสิ่งที่ต้องทำ |
|---|--------|--------|---------------|----------------------|
| 1 | เปลี่ยน `JWT_SECRET_KEY` จากค่าตั้งต้น | ❌ | `.env` | ค่าปัจจุบัน `super_secret_jwt_key_change_me_in_production` — ต้องสร้าง key แบบ random ที่แข็งแกร่ง |
| 2 | จำกัด CORS origins ให้เจาะจง | ❌ | `main.py` | ตอนนี้เปิด `allow_origins=["*"]` — ต้องระบุ domain จริงของ Wix site |
| 3 | ปิด/ลบเบอร์ทดสอบ 087 bypass | ❌ | `routers/auth.py`, `data_service.py` | ตอนนี้เบอร์ `087*` ข้าม SMS Gateway ทุกกรณี — ต้องปิดเมื่อขึ้น production |

---

## 🥈 ส่วนที่ 3: Phase 2 — Social Matchmaking & Advanced Features

เน้นยกระดับคอมมูนิตี้ ฟังก์ชันอัจฉริยะ และระบบอัตโนมัติ

---

### 3.1 ระบบล็อกอินด้วย Google OAuth (SSO)

| # | รายการ | สถานะ | ไฟล์ที่เกี่ยวข้อง | รายละเอียด |
|---|--------|--------|-------------------|------------|
| 1 | Endpoint `POST /api/v1/auth/google` (โครงสร้าง) | 🟡 | `routers/auth.py` | **มี Endpoint แล้ว** แต่ตอนนี้ hardcode email/username/google_id จำลองตายตัว ไม่ได้ verify id_token จริง |
| 2 | **ต่อท่อ Google ID Token Verification จริง** | ❌ | `routers/auth.py` | ต้องใช้ `google-auth` library เรียก `id_token.verify_oauth2_token()` เพื่อถอดข้อมูลจริงจาก Google |
| 3 | เพิ่ม Google OAuth credentials ใน `.env` | ❌ | `.env` | เช่น `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` |

---

### 3.2 อัลกอริทึมจับคู่ผู้เล่น (NTRP Matchmaking)

| # | รายการ | สถานะ | ไฟล์ที่เกี่ยวข้อง | รายละเอียด |
|---|--------|--------|-------------------|------------|
| 1 | Endpoint `POST /api/v1/matching/find` (โครงสร้าง) | 🟡 | `routers/matching.py` | **มี Endpoint แล้ว** — ค้นหาผู้เล่นตาม `ntrp_min`-`ntrp_max` + `playing_style` จาก mock data แล้วสร้าง match post |
| 2 | **พัฒนา Algorithm เต็มรูปแบบ** | ❌ | `data_service.py` | ต้องเพิ่มเงื่อนไขกรอง: `match_preference` (equal/higher/lower), ระยะทาง, ตารางเวลาว่าง, ประวัติเคยเล่นด้วย |
| 3 | ระบบเข้าร่วม/ตอบรับแมตช์ | ❌ | `routers/matching.py` | ยังไม่มี Endpoint ให้ผู้เล่นอื่นกด "เข้าร่วม" แมตช์ที่เปิดอยู่ |
| 4 | ระบบเปลี่ยนสถานะแมตช์ | ❌ | `data_service.py` | ยังไม่มี logic สำหรับเปลี่ยน match status จาก `open` → `matched` → `completed` |

---

### 3.3 ระบบรีวิวผู้เล่น (UGC Loop)

| # | รายการ | สถานะ | ไฟล์ที่เกี่ยวข้อง | รายละเอียด |
|---|--------|--------|-------------------|------------|
| 1 | Endpoint `POST /api/v1/matches/{id}/reviews` (โครงสร้าง) | 🟡 | `routers/reviews.py` | **มี Endpoint แล้ว** — รับ `reviewee_id` + `rating` (1-5) + `comment` แล้วบันทึกลง mock_reviews |
| 2 | **คำนวณคะแนนเฉลี่ยดาวสะสม** | ❌ | `data_service.py` | ต้องเขียน logic สำหรับ aggregate ค่าเฉลี่ย rating แล้ว update กลับไปที่ profile ของ `reviewee_id` |
| 3 | Guard: ตรวจว่า reviewer เป็นผู้เล่นในแมตช์จริง | ❌ | `routers/reviews.py` | ตอนนี้ไม่มีการตรวจว่า match_id นั้นมีจริงหรือไม่ และ reviewer เคยเล่นใน match นั้นหรือเปล่า |
| 4 | Guard: ป้องกันรีวิวซ้ำ | ❌ | `data_service.py` | ตอนนี้ user คนเดิมสามารถรีวิวคนเดิมในแมตช์เดิมซ้ำได้ไม่จำกัด |
| 5 | Endpoint ดูรีวิวของผู้เล่น | ❌ | `routers/reviews.py` | ยังไม่มี `GET` endpoint สำหรับดึงรีวิวทั้งหมดของผู้เล่นคนหนึ่ง |

---

### 3.4 ระบบสแกนสลิปอัตโนมัติ (Auto Slip OCR)

| # | รายการ | สถานะ | ไฟล์ที่เกี่ยวข้อง | รายละเอียด |
|---|--------|--------|-------------------|------------|
| 1 | เลือกผู้ให้บริการ Slip OCR | ❌ | — | ตัดสินใจระหว่าง **Easy Slip API** / **SlipOK API** |
| 2 | สร้าง `app/services/slip_verification_service.py` | ❌ | ไฟล์ใหม่ | เขียน Service ส่งรูปสลิปไป OCR → ได้ยอดเงิน + วันเวลาโอน |
| 3 | แก้ไข Flow หลังอัปโหลดสลิป | ❌ | `routers/payments.py` | หลังอัปโหลดสลิป → ส่งไป OCR → ถ้ายอดตรง → อัปเดต booking เป็น `confirmed` อัตโนมัติ ไม่ต้องรอ Admin |
| 4 | Fallback: ถ้า OCR ล้มเหลว → ส่งให้ Admin ตรวจแมนนวล | ❌ | `routers/payments.py` | กรณี OCR อ่านไม่ออกหรือ API ล่ม ให้ระบบ fallback กลับไปเป็น `processing` (รอ Admin) |

---

## 🛍️ ส่วนที่ 4: Phase 3 — Marketplace & Service Expansion

ยังไม่ต้องเริ่มทำตอนนี้ แต่ลิสต์ไว้เพื่อให้เห็นภาพรวม

| # | รายการ | สถานะ | รายละเอียด |
|---|--------|--------|------------|
| 1 | ระบบจองโค้ช (Coach Booking) | ❌ | เพิ่ม Collection `coaches` + Endpoint จองเวลาซ้อม |
| 2 | ระบบ Member Tier / Privilege | ❌ | สิทธิพิเศษตาม tier (Silver/Gold/Platinum) |
| 3 | ระบบ Member Pricing | ❌ | ราคาพิเศษสำหรับสมาชิก |
| 4 | ระบบขายสินค้าในสนาม (Storefront) | ❌ | Mini e-commerce สำหรับน้ำ อุปกรณ์เทนนิส |
| 5 | ระบบ Voucher Redeem | ❌ | กรอกโค้ดลดราคา/คูปอง |
| 6 | Service Marketplace (Digital Service Layer) | ❌ | บริการเสริม เช่น เช่าผู้เล่นมือโปร |

---

## 📊 สรุปสถานะรวมทุกเฟส

| เฟส | รวมรายการ | ✅ เสร็จ | 🟡 Mock | ❌ ยังไม่ทำ |
|-----|-----------|---------|---------|------------|
| **ส่วนที่ 0: Foundation** | 16 | 16 | 0 | 0 |
| **ส่วนที่ 1: Phase 1 MVP** | 24 | 19 | 5 | 0 |
| **ส่วนที่ 2: Phase 1.5 Go-Live** | 13 | 0 | 0 | 13 |
| **ส่วนที่ 3: Phase 2 Features** | 14 | 0 | 3 | 11 |
| **ส่วนที่ 4: Phase 3 Marketplace** | 6 | 0 | 0 | 6 |
| **รวมทั้งหมด** | **73** | **35** | **8** | **30** |

> **สรุป: ทำเสร็จแล้ว 35 รายการ (48%), ทำแค่โครงสร้าง Mock 8 รายการ (11%), ยังไม่ได้ทำ 30 รายการ (41%)**

---

## 🎯 ลำดับงานที่ควรทำต่อ (Recommended Next Steps)

```
┌─────────────────────────────────────────────────┐
│  ขั้นที่ 1: เชื่อมต่อ MongoDB จริง (ส่วน 2.1)   │ ← ★ ทำก่อนเป็นอันดับแรก
│  แก้ไข main.py + data_service.py + routers      │    เพราะเป็น Blocker ของทุกอย่าง
├─────────────────────────────────────────────────┤
│  ขั้นที่ 2: เชื่อมต่อ Cloud Storage (ส่วน 2.2)   │ ← ทำควบคู่หรือหลัง DB
│  สร้าง storage_service + แก้ payments router     │
├─────────────────────────────────────────────────┤
│  ขั้นที่ 3: ความปลอดภัย Production (ส่วน 2.3)   │ ← ก่อน Deploy จริง
│  JWT key จริง + CORS + ปิด 087 bypass            │
├─────────────────────────────────────────────────┤
│  ขั้นที่ 4: Google OAuth จริง (ส่วน 3.1)         │ ← เริ่ม Phase 2
├─────────────────────────────────────────────────┤
│  ขั้นที่ 5: Matchmaking Algorithm (ส่วน 3.2)     │
├─────────────────────────────────────────────────┤
│  ขั้นที่ 6: UGC Reviews + Auto Slip (ส่วน 3.3-4)│
├─────────────────────────────────────────────────┤
│  ขั้นที่ 7: Phase 3 Marketplace (ส่วน 4)         │ ← อนาคต
└─────────────────────────────────────────────────┘
```

---

> 📝 **หมายเหตุ:** เอกสารฉบับนี้จะถูกอัปเดตเมื่อมีการทำงานเสร็จ ให้เปลี่ยนสถานะจาก ❌ → 🟡 → ✅ พร้อมใส่วันที่ที่ทำเสร็จ เพื่อให้ทีมติดตามได้ตลอด

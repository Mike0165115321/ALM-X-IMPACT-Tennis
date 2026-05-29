# 📘 คู่มือการเชื่อมต่อและบริหารจัดการหลังบ้าน (Developer Operations & Integration Handbook)

เอกสารฉบับนี้จัดทำขึ้นเพื่อรวบรวม **"ข้อมูลทางเทคนิคสำคัญ"** สำหรับระบบส่ง SMS OTP, การตั้งค่าตัวแปรระบบในไฟล์ `.env` และการเข้าถึงระบบไฟล์ Log ย้อนหลัง เพื่อให้ผู้ดูแลระบบและทีมพัฒนาในอนาคตสามารถเข้ามาตรวจสอบ แก้ไข และขยายระบบได้อย่างรวดเร็ว

---

## 📞 1. ระบบส่ง SMS OTP (ThaiBulkSMS OTP API V1)

ระบบยืนยันตัวตนผ่านโทรศัพท์มือถือใช้ **บริการ OTP สำเร็จรูป (OTP Ready to Use)** ของเครือข่าย ThaiBulkSMS โดยเชื่อมต่อกับเซิร์ฟเวอร์หลักผ่านทาง API V1 (ปลอดภัยสูง รวดเร็ว และประหยัดค่าใช้จ่าย)

### 📡 รายละเอียด API Endpoint และพารามิเตอร์การต่อท่อ:

#### **A. ขั้นตอนส่งคำขอ OTP (Request OTP)**
*   **API URL ปลายทาง:** `https://otp.thaibulksms.com/v1/otp/request`
*   **Request Method:** `POST`
*   **Query Parameters / URL Encoded:**
    *   `key`: App Key ประจำแอปพลิเคชัน (ได้จาก OTP Manager ของหน้าเว็บ)
    *   `secret`: App Secret ประจำแอปพลิเคชัน
    *   `msisdn`: เบอร์โทรศัพท์มือถือผู้รับ (ต้องเปลี่ยนเป็นฟอร์แมตสากล เช่น `66968013963`)
*   **Response (200 OK):**
    ```json
    {
      "status": "success",
      "data": {
        "token": "wzRX5a3GVyLrJbwt7iVNNQ1W0eApqO2P8",
        "refno": "NLCA",
        "expire": "2026-05-27 12:05:00"
      }
    }
    ```
    *(หลังบ้านจะทำการบันทึกค่า `token` ตัวนี้ลงในเซสชันชั่วคราวของเบอร์โทรศัพท์นั้นๆ เพื่อใช้ในขั้นตอนการตรวจสอบถัดไป)*

#### **B. ขั้นตอนตรวจสอบความถูกต้องของรหัส (Verify OTP)**
*   **API URL ปลายทาง:** `https://otp.thaibulksms.com/v1/otp/verify`
*   **Request Method:** `POST`
*   **Query Parameters / URL Encoded:**
    *   `key`: App Key ประจำแอปพลิเคชัน
    *   `secret`: App Secret ประจำแอปพลิเคชัน
    *   `token`: รหัส Token อ้างอิงที่ได้รับกลับมาจากขั้นตอนส่งคำขอ (Request Step)
    *   `pin`: รหัสตัวเลข 6 หลักที่ผู้ใช้กรอกเข้ามา
*   **Response (200 OK):**
    ```json
    {
      "status": "success",
      "data": {
        "status": "success",
        "message": "Verify successfully."
      }
    }
    ```

---

## ⚙️ 2. การตั้งค่าตัวแปรระบบ (Environment Variables - `.env`)

ไฟล์สำหรับบันทึกคีย์ความปลอดภัยทั้งหมดของระบบหลังบ้านอยู่ที่รูทของโครงการหลังบ้าน คือไฟล์ [.env](file:///c:/GitHub/ALM-X-IMPACT-Tennis/backend/.env)

| ชื่อตัวแปร (Key) | หน้าที่และความสำคัญ | ค่าที่ตั้งไว้ (ตัวอย่าง) |
| :--- | :--- | :--- |
| `PORT` | พอร์ตสำหรับการรันหลังบ้านในเครื่องของท่าน | `8000` |
| `HOST` | ไอพีแอดเดรสสำหรับผูกการเชื่อมต่อ | `0.0.0.0` (ยอมรับทุกการเชื่อมต่อ) |
| `SUPABASE_DB_URL` | ลิงก์ปลายทางเชื่อมต่อฐานข้อมูล Supabase Cloud (PostgreSQL) | `postgresql+asyncpg://postgres:PASSWORD@db.xxx.supabase.co:5432/postgres` |
| `JWT_SECRET_KEY` | รหัสลับความปลอดภัยสำหรับใช้เข้ารหัส Token สมาชิก | `super_secret_jwt_key_change_me_in_production` |
| `SMS_API_KEY` | App Key ประจำแอปพลิเคชัน OTP จาก ThaiBulkSMS | `17798576284341` |
| `SMS_API_SECRET` | App Secret ประจำแอป OTP จาก ThaiBulkSMS | `b60f404535a699f6866a46dd83975865` |
| `SMS_SENDER_NAME` | ชื่อผู้ส่งที่จะปรากฏบนมือถือของผู้ใช้ | `OTP_SMS` (ผู้ส่งเริ่มต้นทดสอบฟรี) |
| `SMS_OTP_API_URL` | โฮสต์เชื่อมต่อระบบ OTP ของผู้บริการ | `https://otp.thaibulksms.com/v1/otp` |

---

## 📝 3. ระบบจัดเก็บไฟล์ Log หมุนสลับอัตโนมัติ (Advanced Logging System)

เพื่ออำนวยความสะดวกในการ **ตรวจสอบบั๊ก (Debugging) และส่องดูย้อนหลังเมื่อระบบมีปัญหาบน Production** ระบบหลังบ้านได้รับการติดตั้งตัว Logger ประสิทธิภาพสูง:

### 📁 ตำแหน่งจัดเก็บไฟล์ Log:
*   ไฟล์จะถูกสร้างและเก็บไว้ที่โฟลเดอร์ **`backend/logs/app.log`**

### ⚙️ คุณสมบัติเด่นของระบบบันทึก Log:
1.  **Console + File Logger**: แสดงผลแบบย่อบน Console ของนักพัฒนาเพื่อง่ายต่อการอ่าน และจัดเก็บข้อมูลอย่างละเอียดลงในไฟล์ `app.log`
2.  **Rotating File Handler (ระบบป้องกันฮาร์ดดิสก์เต็ม)**: 
    *   ไฟล์ `app.log` จะมีขนาดไฟล์สูงสุดไม่เกิน **5 Megabytes (5MB)**
    *   หากขนาดไฟล์เกิน 5MB ระบบจะทำการตัดและสลับสร้างไฟล์สำรองให้โดยอัตโนมัติ (เช่น `app.log.1`, `app.log.2`) และจะเก็บสำรองย้อนหลังไว้สูงสุดเพียง **5 ไฟล์**
    *   *ข้อดี:* ป้องกันไม่ให้ไฟล์ Log ขยายใหญ่เกินไปจนทำให้พื้นที่ดิสก์ของเซิร์ฟเวอร์เต็มอย่างถาวร

### 🔍 ตัวอย่างข้อมูล Log ที่ถูกเก็บบันทึกจริงในไฟล์:
```text
[2026-05-27 12:03:18] INFO in sms_service: 📲 กำลังยิงคำขอ OTP ไปยังเบอร์ 0968013963 ผ่าน OTP Gateway...
[2026-05-27 12:03:20] INFO in _client: HTTP Request: POST https://otp.thaibulksms.com/v1/otp/request?key=... "HTTP/1.1 200 OK"
[2026-05-27 12:03:20] INFO in sms_service: ✅ ส่งคำขอ OTP สำเร็จ! (Token: wzRX5a3GVyLrJbwt7iVNNQ1W0eApqO2P8)
[2026-05-27 12:08:05] ERROR in data_service: ❌ [Network Error] ไม่สามารถยืนยัน OTP กับ SMS Gateway ได้: Connection timeout
```

---

## 🛠️ 4. การจัดการกรณีเกิด Exception (Custom Exception Handling)

ระบบมีการดักจับและโยน Exception เฉพาะตัวผ่านโมดูล [exceptions.py](file:///c:/GitHub/ALM-X-IMPACT-Tennis/backend/app/exceptions.py) เพื่อให้ปลายทาง (เช่นหน้าบ้าน Wix หรือ API Client) สามารถนำไปประมวลผลต่อได้ง่ายขึ้น:

*   **`SMSGatewayException`**: ถูกโยนเมื่อเน็ตหลุด ไม่สามารถเชื่อมต่อกับ ThaiBulkSMS ได้ หรือส่ง OTP ไม่ผ่าน (HTTP 502 Bad Gateway)
*   **`SlotConflictException`**: ถูกโยนเมื่อสล็อตเวลานั้นมีคนจองไปแล้ว (HTTP 409 Conflict)
*   **`UserDuplicateBookingException`**: ถูกโยนเมื่อผู้ใช้คนเดิมกดจองสนามสล็อตเดิมซ้ำ (HTTP 400 Bad Request)

---

## 📂 5. ระบบจัดเก็บไฟล์รูปสลิป (Storage Service & File Uploads)

ระบบการอัปโหลดไฟล์ภาพสลิปโอนเงิน ได้รับการออกแบบโครงสร้างตามหลัก **Decoupled Architecture** เพื่ออำนวยความสะดวกในการเปลี่ยนผ่านระบบจัดเก็บไฟล์ในอนาคต:

### ⚙️ สถาปัตยกรรมและการทำงานปัจจุบัน (Local Storage Simulation):
1.  **บริการอิสระ (`StorageService`):** ควบคุมและดูแลผ่านคลาส [storage_service.py](file:///c:/GitHub/ALM-X-IMPACT-Tennis/backend/app/services/storage_service.py) เพียงจุดเดียว
2.  **การบันทึกไฟล์จริง:** ในเฟสจำลองนี้ ระบบจะนำรูปสลิปจาก Request บันทึกตรงลงโฟลเดอร์ **`backend/uploads/`** ในฮาร์ดดิสก์หลังบ้าน พร้อมสร้างชื่อไฟล์เฉพาะเพื่อความปลอดภัย: `{booking_id}_{timestamp}_{uuid_hex}.png`
3.  **การบริการ Static Files:** เมื่อเปิดเซิร์ฟเวอร์ ระบบจะนำเข้า `StorageService.init_app(app)` เพื่อสร้างโฟลเดอร์และเปิดท่อบริการไฟล์ภาพทางช่องทาง Static HTTP ทำให้เปิดลิงก์รูปสลิปดูบนเบราว์เซอร์ได้ทันที
4.  **Base URL แบบไดนามิก:** รูปสลิปจะถูกส่งกลับไปในรูปแบบลิงก์เต็มรูปแบบ เช่น `http://localhost:8000/uploads/filename.png` อ้างอิงตามเซิร์ฟเวอร์ที่กำลังทำงานอยู่ ณ ขณะนั้นจริง

### 🚀 วิธีการเปลี่ยนผ่านสู่ Google Cloud Storage / AWS S3 ในอนาคต:
เมื่อเข้าสู่โปรดักชันและต้องการบันทึกสลิปขึ้น Cloud Bucket จริง **เราแก้ไขเฉพาะที่ไฟล์บริการนี้เท่านั้นโดยไม่กระทบจุดอื่นเลย**:
1.  เข้าไปที่ [storage_service.py](file:///c:/GitHub/ALM-X-IMPACT-Tennis/backend/app/services/storage_service.py)
2.  แก้ไขฟังก์ชัน `init_app(app)` เพื่อทำหน้าที่สร้างการเชื่อมต่อเริ่มต้นกับ Google Cloud Storage SDK หรือ S3 Client
3.  แก้ไขฟังก์ชัน `upload_slip(slip_file, booking_id, request)` ให้ทำหน้าที่เปลี่ยนจากการเขียนไฟล์ลงเครื่อง (`open(file, "wb")`) ไปเป็น **`storage_client.upload_from_file(...)`** และส่ง URL จริงของ Cloud Storage กลับไปแทน
4.  *ผลลัพธ์:* โค้ดในฝั่งของ API / Routers และ `main.py` จะยังคงทำงานได้ปกติโดยไม่มีการแก้ไขแม้แต่บรรทัดเดียว!


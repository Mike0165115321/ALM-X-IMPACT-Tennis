# 🎾 คู่มือการเชื่อมต่อระบบจองสนามบน Wix Velo (FastAPI Court Booking Integration Guide)
> อัปเดตล่าสุด: 28 พฤษภาคม 2026

คู่มือฉบับนี้จัดทำขึ้นเพื่อให้นักพัฒนาฝั่งหน้าบ้าน (Wix Velo Developer) สามารถคัดลอกและนำไปใช้เชื่อมต่อปุ่มกดจองสล็อตสนามในหน้า **Courts** หรือหน้ารายละเอียดการจอง ส่งตรงมายังหลังบ้าน FastAPI ได้อย่างรวดเร็วและปลอดภัย 100%

---

## 🏗️ 1. โครงสร้างการส่งข้อมูลการจอง (REST API Contract)

*   **API Endpoint ปลายทาง:** `${BACKEND_URL}/api/v1/queues/book`
*   **Request Method:** `POST`
*   **Authentication:** จำเป็นต้องแนบ Bearer Token (JWT) ใน Headers
*   **รูปแบบข้อมูล JSON (Payload):**
    ```json
    {
      "court_id": "60d5ec4b2f8fb8123456789d",
      "booking_date": "2026-05-30",
      "time_slot": "16:00-17:00"
    }
    ```

---

## 🔑 2. การจัดการ JWT Token ในฝั่ง Wix Velo

ในการจองสนาม หลังบ้านจำเป็นต้องทราบว่า **"ผู้เล่นคนใดเป็นคนจอง"** ผ่านการถอดรหัส Token 
ดังนั้นฝั่ง Wix จะต้องเก็บ Token ไว้ในหน่วยความจำหลังจากผู้ใช้ล็อกอินสำเร็จ:

```javascript
import { local } from 'wix-storage';

// 💡 ตอนล็อกอินสำเร็จ (Login Page):
// บันทึก Token ที่ได้จาก API ลงบราวเซอร์ลูกค้า
local.setItem("userToken", jsonResponse.access_token);
local.setItem("isPhoneVerified", jsonResponse.user.is_phone_verified ? "yes" : "no");
```

---

## 💻 3. โค้ด Wix Velo เต็มรูปแบบสำหรับปุ่ม "กดจองสนาม"

คัดลอกโค้ดนี้ไปประยุกต์ใช้งานในหน้า **Courts** ของ Wix เมื่อมีการคลิกปุ่มสล็อตเวลา (เช่น ปุ่มจองสล็อต 16:00-17:00):

```javascript
import { fetch } from 'wix-fetch';
import { local } from 'wix-storage';
import wixLocation from 'wix-location';

// 🔗 แก้ไข URL ตัวนี้ตามลิงก์สาธารณะที่รันหลังบ้าน
const BACKEND_URL = "https://your-tunnel-subdomain.localtunnel.me"; 

/**
 * ฟังก์ชันหลักในการกดจองสล็อตเวลา
 * @param {string} courtId - ไอดีของสนามที่เลือกจอง
 * @param {string} bookingDate - วันที่จอง รูปแบบ "YYYY-MM-DD"
 * @param {string} timeSlot - ช่วงเวลา เช่น "16:00-17:00"
 */
export function bookCourtSlot(courtId, bookingDate, timeSlot) {
    // 1. ดึง Token และสถานะเช็คเบอร์มือถือของลูกค้าจากบราวเซอร์
    const token = local.getItem("userToken");
    const isPhoneVerified = local.getItem("isPhoneVerified");

    // 2. Guard: ตรวจสอบการลงชื่อเข้าใช้งานเบื้องต้น
    if (!token) {
        showVisualAlert("กรุณาเข้าสู่ระบบก่อนจองสนาม", "warning");
        wixLocation.to("/login"); // พาส่งไปหน้า Login
        return;
    }

    // 3. Guard: ตรวจสอบความปลอดภัยว่ายืนยันเบอร์ด้วย OTP หรือยัง
    if (isPhoneVerified !== "yes") {
        showVisualAlert("กรุณายืนยันเบอร์โทรศัพท์ด้วยรหัส OTP ก่อนทำการจอง", "error");
        wixLocation.to("/otp-verify"); // พาส่งไปหน้ากรอก OTP
        return;
    }

    console.log(`กำลังทำรายการส่งจองสนาม ID: ${courtId} ในวันที่: ${bookingDate} สล็อต: ${timeSlot}`);
    startLoadingSpinner(); // เปิดเอฟเฟกต์หมุนรอระบบทำงาน

    // 4. ต่อท่อยิง API แบบ Asynchronous ไปที่ FastAPI หลังบ้าน
    fetch(`${BACKEND_URL}/api/v1/queues/book`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}` // แนบเหรียญรหัสสิทธิ์ยืนยันตัวตน
        },
        body: JSON.stringify({
            court_id: courtId,
            booking_date: bookingDate,
            time_slot: timeSlot
        })
    })
    .then((httpResponse) => {
        stopLoadingSpinner(); // ปิดเอฟเฟกต์หมุนรอ

        // 5. วิเคราะห์ HTTP Status Code ที่ตอบกลับจาก FastAPI
        if (httpResponse.status === 201) {
            return httpResponse.json(); // จองสำเร็จ
        } 
        
        return httpResponse.json().then((errorJSON) => {
            // ดึงข้อความแจ้งเตือนภาษาไทยจากหลังบ้าน
            const errorMsg = errorJSON.detail || "การทำรายการจองล้มเหลว";
            
            if (httpResponse.status === 409) {
                // กรณีเกิดการกดแย่งชิงสล็อตเดียวกันในเวลาเดียวกัน (Slot Conflict)
                showVisualAlert("ขออภัย! สล็อตเวลานี้พึ่งโดนผู้อื่นจองตัดหน้าไปเมื่อสักครู่", "warning");
            } else if (httpResponse.status === 401) {
                showVisualAlert("สิทธิ์การใช้งานหมดอายุ กรุณาเข้าสู่ระบบใหม่อีกครั้ง", "error");
                wixLocation.to("/login");
            } else {
                showVisualAlert(errorMsg, "error");
            }
            return Promise.reject(errorMsg);
        });
    })
    .then((bookingResponse) => {
        console.log("จองสำเร็จเสร็จสิ้น! ข้อมูลตอบกลับ:", bookingResponse);
        
        // 💾 บันทึก ID การจองเพื่อใช้ในขั้นตอนการอัปโหลดสลิปเงินถัดไป
        local.setItem("currentBookingId", bookingResponse.booking_id);

        showVisualAlert("สร้างรายการจองสำเร็จแล้ว! กำลังนำคุณไปหน้าโอนเงินชำระค่าบริการ", "success");
        
        // ➡️ นำทางผู้ใช้ไปยังหน้าอัปโหลดรูปสลิปพร้อมส่งค่า Booking ID ไปทาง URL
        setTimeout(() => {
            wixLocation.to(`/payment?booking_id=${bookingResponse.booking_id}`);
        }, 1500);
    })
    .catch((err) => {
        console.error("เกิดข้อผิดพลาดในการจอง:", err);
    });
}

// ----------------- ฟังก์ชันเสริมสำหรับ UI (Helper Functions) -----------------

function showVisualAlert(message, type) {
    // นำข้อความแจ้งเตือนไปโชว์ในกล่องแจ้งเตือนของหน้าเว็บ Wix
    // เช่น $w("#textAlert").text = message; $w("#boxAlert").show();
    console.log(`[ALERT] [${type.toUpperCase()}] ${message}`);
}

function startLoadingSpinner() {
    // แสดงโหลดดิ้ง $w("#spinner").show();
}

function stopLoadingSpinner() {
    // ปิดโหลดดิ้ง $w("#spinner").hide();
}

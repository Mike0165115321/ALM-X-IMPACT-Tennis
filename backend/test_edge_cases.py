import pytest
from fastapi.testclient import TestClient
from main import app
from app.services.mock_db import mock_users, mock_otp_store
from app.exceptions import SMSGatewayException, SlotConflictException

client = TestClient(app)

# ----------------- 👥 Auth Register Edge Cases -----------------

def test_register_duplicate_email():
    """
    ทดสอบการสมัครสมาชิกซ้ำด้วยอีเมลเดิมที่มีอยู่แล้วในระบบ
    """
    payload = {
        "username": "somchai_dup",
        "email": "user1@example.com",  # อีเมลที่มีใน Seed Data (somchai)
        "password": "securepassword123",
        "phone": "0811112222"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "อีเมลนี้ถูกใช้งานแล้ว" in response.json()["detail"]

def test_register_invalid_password_length():
    """
    ทดสอบรหัสผ่านที่สั้นเกินไป (ต่ำกว่า 8 อักษร)
    """
    payload = {
        "username": "short_pwd",
        "email": "short@example.com",
        "password": "short",  # 5 ตัวอักษร
        "phone": "0811112222"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422  # Validation Error

def test_register_invalid_thai_phone_format():
    """
    ทดสอบกรอกเบอร์โทรศัพท์ผิดฟอร์แมตเบอร์ไทย 10 หลัก
    """
    payload = {
        "username": "bad_phone",
        "email": "phone@example.com",
        "password": "securepassword123",
        "phone": "12345"  # ไม่ขึ้นต้นด้วย 0 และความยาวไม่เท่ากับ 10 หลัก
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422

# ----------------- 📅 Court Available Edge Cases -----------------

def test_list_courts_invalid_date_format():
    """
    ทดสอบดึงข้อมูลสนามด้วยรูปแบบวันที่ไม่ถูกต้อง
    """
    response = client.get("/api/v1/courts?date=27-05-2026")  # ควรเป็น YYYY-MM-DD
    assert response.status_code == 400
    assert "รูปแบบวันที่ไม่ถูกต้อง" in response.json()["detail"]

# ----------------- 📅 Queues & Booking Edge Cases -----------------

def test_book_non_existent_court():
    """
    ทดสอบจองสนามที่ไม่มีตัวตนจริงในระบบ (Court ID มั่ว)
    """
    # สมัครและยืนยันเบอร์โทรศัพท์เพื่อพร้อมจอง
    reg_payload = {
        "username": "no_court_user",
        "email": "nocourt@example.com",
        "password": "securepassword123",
        "phone": "0871112222"
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # ส่งคำขอ OTP ก่อนเพื่อให้ระบบสุ่มรหัสเก็บบันทึกไว้ใน mock_otp_store
    client.post("/api/v1/auth/otp/send", json={"phone": "0871112222"})
    
    # ยืนยัน OTP จำลองก่อนเพื่อปลดล็อคสิทธิ์จอง
    otp_entry = mock_otp_store["0871112222"]
    client.post("/api/v1/auth/otp/verify", json={
        "phone": "0871112222",
        "otp_code": otp_entry["otp_code"],
        "ref_code": otp_entry["ref_code"]
    })

    # ส่งคำขอจองคิวสนาม ID มั่ว
    booking_payload = {
        "court_id": "non_existent_id_12345",
        "booking_date": "2026-05-30",
        "time_slot": "16:00-17:00"
    }
    response = client.post("/api/v1/queues/book", json=booking_payload, headers=headers)
    assert response.status_code == 404
    assert "ไม่พบสนามที่ระบุ" in response.json()["detail"]

def test_book_without_otp_verified_phone():
    """
    ทดสอบจองคิวสนามโดยที่เบอร์โทรศัพท์ยังไม่ได้กดยืนยัน OTP
    """
    reg_payload = {
        "username": "unverified_player",
        "email": "unverified@example.com",
        "password": "securepassword123",
        "phone": "0872223333"
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    booking_payload = {
        "court_id": "60d5ec4b2f8fb8123456789d",
        "booking_date": "2026-05-30",
        "time_slot": "16:00-17:00"
    }
    response = client.post("/api/v1/queues/book", json=booking_payload, headers=headers)
    assert response.status_code == 403
    assert "กรุณายืนยันเบอร์โทรศัพท์ด้วย OTP" in response.json()["detail"]

# ----------------- 💳 Payments Slip Edge Cases -----------------

def test_upload_invalid_slip_file_type():
    """
    ทดสอบอัปโหลดไฟล์สลิปชำระเงินที่นามสกุลไม่ใช่รูปภาพ (เช่น ไฟล์ .pdf)
    """
    # สมัครสมาชิก
    reg_payload = {
        "username": "pdf_uploader",
        "email": "pdf@example.com",
        "password": "securepassword123",
        "phone": "0873334444"
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    file_content = b"fake-pdf-content"
    files = {"slip_file": ("slip.pdf", file_content, "application/pdf")}
    form_data = {"booking_id": "booking_1", "amount": 500.0}
    
    response = client.post("/api/v1/payments/pay", data=form_data, files=files, headers=headers)
    assert response.status_code == 400
    assert "กรุณาอัปโหลดไฟล์รูปภาพสลิปที่ถูกต้อง" in response.json()["detail"]

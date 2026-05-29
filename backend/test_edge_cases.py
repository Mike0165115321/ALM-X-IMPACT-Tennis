import pytest
import random
from fastapi.testclient import TestClient
from main import app
from app.services.otp_store import otp_store as mock_otp_store
from app.exceptions import SMSGatewayException, SlotConflictException

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def get_unique_user_payload(base_username: str):
    num = random.randint(1000000, 9999999)
    return {
        "username": f"{base_username}_{num}",
        "email": f"{base_username}_{num}@example.com",
        "password": "supersecurepassword123",
        "phone": f"087{num}"
    }

# ----------------- 👥 Auth Register Edge Cases -----------------

def test_register_duplicate_email(client):
    """
    ทดสอบการสมัครสมาชิกซ้ำด้วยอีเมลเดิมที่มีอยู่แล้วในระบบ
    """
    payload = {
        "username": "somchai_dup",
        "email": "high_working@hotmail.com",  # อีเมลที่มีใน Seed Data จริง
        "password": "securepassword123",
        "phone": "0811112222"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "อีเมลนี้ถูกใช้งานแล้ว" in response.json()["detail"]

def test_register_invalid_password_length(client):
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

def test_register_invalid_thai_phone_format(client):
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

def test_list_courts_invalid_date_format(client):
    """
    ทดสอบดึงข้อมูลสนามด้วยรูปแบบวันที่ไม่ถูกต้อง
    """
    response = client.get("/api/v1/courts?date=27-05-2026")  # ควรเป็น YYYY-MM-DD
    assert response.status_code == 400
    assert "รูปแบบวันที่ไม่ถูกต้อง" in response.json()["detail"]

# ----------------- 📅 Queues & Booking Edge Cases -----------------

def test_book_non_existent_court(client):
    """
    ทดสอบจองสนามที่ไม่มีตัวตนจริงในระบบ (Court ID มั่ว)
    """
    # สมัครและยืนยันเบอร์โทรศัพท์เพื่อพร้อมจอง
    reg_payload = get_unique_user_payload("no_court_user")
    phone = reg_payload["phone"]
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # ส่งคำขอ OTP ก่อนเพื่อให้ระบบสุ่มรหัสเก็บบันทึกไว้ใน mock_otp_store
    client.post("/api/v1/auth/otp/send", json={"phone": phone})
    
    # ยืนยัน OTP จำลองก่อนเพื่อปลดล็อคสิทธิ์จอง
    otp_entry = mock_otp_store[phone]
    client.post("/api/v1/auth/otp/verify", json={
        "phone": phone,
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

def test_book_without_otp_verified_phone(client):
    """
    ทดสอบจองคิวสนามโดยที่เบอร์โทรศัพท์ยังไม่ได้กดยืนยัน OTP
    """
    reg_payload = get_unique_user_payload("unverified_player")
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

def test_upload_invalid_slip_file_type(client):
    """
    ทดสอบอัปโหลดไฟล์สลิปชำระเงินที่นามสกุลไม่ใช่รูปภาพ (เช่น ไฟล์ .pdf)
    """
    # สมัครสมาชิก
    reg_payload = get_unique_user_payload("pdf_uploader")
    phone = reg_payload["phone"]
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # ยืนยัน OTP จำลองก่อนเพื่อปลดล็อคสิทธิ์จอง
    client.post("/api/v1/auth/otp/send", json={"phone": phone})
    otp_entry = mock_otp_store[phone]
    client.post("/api/v1/auth/otp/verify", json={
        "phone": phone,
        "otp_code": otp_entry["otp_code"],
        "ref_code": otp_entry["ref_code"]
    })
    
    # ดึงคอร์ทมาจองจริงเพื่อทำการผ่าน booking guard (M6)
    random_day = random.randint(10, 28)
    booking_date = f"2026-06-{random_day}"
    
    courts_res = client.get(f"/api/v1/courts?date={booking_date}")
    court_id = courts_res.json()[0]["id"]
    
    # จองคอร์ทจริงเพื่อให้ได้ booking_id
    book_res = client.post("/api/v1/queues/book", json={
        "court_id": court_id,
        "booking_date": booking_date,
        "time_slot": "16:00-17:00"
    }, headers=headers)
    booking_id = book_res.json()["booking_id"]
    
    file_content = b"fake-pdf-content"
    files = {"slip_file": ("slip.pdf", file_content, "application/pdf")}
    form_data = {"booking_id": booking_id, "amount": 500.0}
    
    response = client.post("/api/v1/payments/pay", data=form_data, files=files, headers=headers)
    assert response.status_code == 400
    assert "กรุณาอัปโหลดไฟล์รูปภาพสลิปที่ถูกต้อง" in response.json()["detail"]

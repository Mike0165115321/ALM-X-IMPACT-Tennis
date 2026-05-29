import pytest
import random
from fastapi.testclient import TestClient
from main import app
from app.services.otp_store import otp_store as mock_otp_store

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_matchmaking_phone_verification_guard(client):
    """
    ทดสอบว่าหากเบอร์โทรศัพท์ยังไม่ได้ทำการยืนยันตัวตน (is_phone_verified=False)
    เมื่อเรียกค้นหาคู่เล่นหาแมตช์ควรได้ HTTP 400 Bad Request
    """
    random_id = random.randint(100000, 999999)
    email = f"matcher_guard_{random_id}@gmail.com"
    
    # 1. สมัครสมาชิกบัญชีใหม่ (เริ่มต้นยังไม่ยืนยันโทรศัพท์)
    reg_payload = {
        "username": f"user_guard_{random_id}",
        "email": email,
        "password": "securepassword123",
        "phone": f"089{random_id:07d}"
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. ลองเรียก /api/v1/matching/find (ควรได้ 400 ยืนยันเบอร์)
    payload = {
        "court_id": "test-court-id",
        "match_date": "2026-06-01",
        "time_slot": "10:00-11:00",
        "ntrp_min": 1.5,
        "ntrp_max": 4.0
    }
    match_res = client.post("/api/v1/matching/find", json=payload, headers=headers)
    assert match_res.status_code == 400
    assert "ยืนยันตัวตนผ่านเบอร์โทรศัพท์" in match_res.json()["detail"]

def test_matchmaking_success_flow(client):
    """
    ทดสอบการทำงานในการจับคู่ผู้เล่นตามระดับ NTRP และสร้างโพสต์หาคู่เล่นสำเร็จ
    """
    random_id = random.randint(100000, 999999)
    
    # 1. สร้างผู้ใช้ A (Host)
    email_a = f"host_{random_id}@gmail.com"
    phone_a = f"087{random_id:07d}" # ใช้เบอร์ 087 เพื่อข้าม SMS Gateway
    reg_a = client.post("/api/v1/auth/register", json={
        "username": f"host_user_{random_id}",
        "email": email_a,
        "password": "securepassword123",
        "phone": phone_a
    })
    assert reg_a.status_code == 201
    
    # ยืนยัน OTP
    otp_send_res = client.post("/api/v1/auth/otp/send", json={"phone": phone_a})
    assert otp_send_res.status_code == 200
    otp_entry = mock_otp_store[phone_a]
    otp_code = otp_entry["otp_code"]
    ref_code = otp_entry["ref_code"]
    
    verify_a = client.post("/api/v1/auth/otp/verify", json={
        "phone": phone_a,
        "otp_code": otp_code,
        "ref_code": ref_code
    })
    assert verify_a.status_code == 200
    
    # ดึง Token จากการล็อกอิน
    login_a = client.post("/api/v1/auth/login", json={"email": email_a, "password": "securepassword123"})
    assert login_a.status_code == 200
    token_a = login_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}
    
    # 2. สร้างผู้ใช้ B (ผู้เล่น NTRP 3.5 ที่สมบูรณ์แบบ)
    email_b = f"player_b_{random_id}@gmail.com"
    phone_b = f"0871{random_id:06d}"
    reg_b = client.post("/api/v1/auth/register", json={
        "username": f"player_b_{random_id}",
        "email": email_b,
        "password": "securepassword123",
        "phone": phone_b
    })
    assert reg_b.status_code == 201
    
    # ยืนยัน OTP
    otp_send_b = client.post("/api/v1/auth/otp/send", json={"phone": phone_b})
    otp_entry_b = mock_otp_store[phone_b]
    
    verify_b = client.post("/api/v1/auth/otp/verify", json={
        "phone": phone_b,
        "otp_code": otp_entry_b["otp_code"],
        "ref_code": otp_entry_b["ref_code"]
    })
    assert verify_b.status_code == 200
    
    # ดึงรายชื่อสนาม
    courts_res = client.get("/api/v1/courts?date=2026-06-01")
    assert courts_res.status_code == 200
    courts = courts_res.json()
    assert len(courts) > 0
    court_id = courts[0]["id"]
    
    # 3. ผู้ใช้ A เรียกโพสต์จับคู่หาคู่เล่นในช่วง NTRP 1.5 - 4.5
    payload = {
        "court_id": court_id,
        "match_date": "2026-06-01",
        "time_slot": "16:00-17:00",
        "match_type": "singles",
        "ntrp_min": 1.5,
        "ntrp_max": 4.5
    }
    match_res = client.post("/api/v1/matching/find", json=payload, headers=headers_a)
    assert match_res.status_code == 200
    
    data = match_res.json()
    assert "match_id" in data
    assert data["status"] == "open"
    assert "compatible_matches" in data

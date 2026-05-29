import pytest
import random
from fastapi.testclient import TestClient
from main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_google_login_new_user(client):
    """
    ทดสอบการล็อกอินด้วย Google SSO สำหรับผู้ใช้ใหม่
    (ควรสร้างบัญชีใหม่โดยอัตโนมัติ)
    """
    random_id = random.randint(100000, 999999)
    mock_token = f"mock_new_{random_id}"
    
    response = client.post("/api/v1/auth/google", json={"id_token": mock_token})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == f"google_user_new_{random_id}@gmail.com"
    assert data["user"]["role"] == "player"

def test_google_login_merge_account(client):
    """
    ทดสอบการล็อกอินด้วย Google SSO สำหรับบัญชีเดิมที่มีอีเมลนี้อยู่ในระบบอยู่แล้ว
    (ระบบควรทำการผูก Google ID เข้ากับผู้ใช้นั้นทันทีโดยไม่สร้างบัญชีซ้ำซ้อน)
    """
    random_id = random.randint(100000, 999999)
    mock_suffix = f"merge_{random_id}"
    expected_google_email = f"google_user_{mock_suffix}@gmail.com"
    username = f"merge_{random_id}"
    
    # 1. สมัครสมาชิกบัญชีปกติไว้ล่วงหน้าผ่านทาง Endpoint สมัครสมาชิกปกติ
    reg_payload = {
        "username": username,
        "email": expected_google_email,
        "password": "supersecurepassword123",
        "phone": f"081{random_id:07d}"
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    registered_user = reg_res.json()["user"]
    registered_id = registered_user["id"]
    
    # 2. จำลองการล็อกอินด้วย Google SSO ที่มีอีเมลตรงกัน
    mock_token = f"mock_{mock_suffix}"
    response = client.post("/api/v1/auth/google", json={"id_token": mock_token})
    assert response.status_code == 200
    login_data = response.json()
    assert login_data["user"]["id"] == registered_id # ต้องส่งคืน ID ผู้ใช้เดิมที่ Merge แล้ว!
    assert login_data["user"]["email"] == expected_google_email

def test_google_login_invalid_token(client):
    """
    ทดสอบการส่ง Token ที่ผิดรูปแบบ (ไม่ใช่ mock_ และใช้ไม่ได้กับ Google จริง)
    (ควรล้มเหลวและตอบกลับ 400 Bad Request)
    """
    response = client.post("/api/v1/auth/google", json={"id_token": "completely_invalid_token_1234"})
    assert response.status_code == 400
    assert "ล้มเหลว" in response.json()["detail"] or "ไม่ถูกต้อง" in response.json()["detail"]

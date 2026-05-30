import pytest
import random
import asyncio
from fastapi.testclient import TestClient
from main import app
from app.services.otp_store import otp_store as mock_otp_store
from app.services.data_service import DataService

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_initial_member_tier_and_discount(client):
    """
    ทดสอบว่าบัญชีสมัครใหม่จะเริ่มต้นที่ระดับ Standard
    และได้รับค่าธรรมเนียมการจ่ายเงินราคาปกติ 100% (ไม่มีส่วนลด)
    """
    random_id = random.randint(100000, 999999)
    email = f"tier_std_{random_id}@gmail.com"
    phone = f"087{random_id:07d}"
    
    # 1. สมัครสมาชิก
    reg = client.post("/api/v1/auth/register", json={
        "username": f"user_std_{random_id}",
        "email": email,
        "password": "securepassword123",
        "phone": phone
    })
    assert reg.status_code == 201
    
    # ยืนยัน OTP
    otp_res = client.post("/api/v1/auth/otp/send", json={"phone": phone})
    otp_code = mock_otp_store[phone]["otp_code"]
    ref_code = mock_otp_store[phone]["ref_code"]
    client.post("/api/v1/auth/otp/verify", json={
        "phone": phone,
        "otp_code": otp_code,
        "ref_code": ref_code
    })
    
    # ล็อกอิน
    login_res = client.post("/api/v1/auth/login", json={"email": email, "password": "securepassword123"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. ตรวจรายชื่อสนาม
    courts_res = client.get("/api/v1/courts?date=2026-06-01")
    court_id = courts_res.json()[0]["id"]
    base_price = courts_res.json()[0]["price_per_hour"]
    
    # 3. ส่งคำขอจองคิวสนามด้วยวันเวลาสุ่มเพื่อหลีกเลี่ยงการชนกันบน Supabase Cloud
    random_day = random.randint(10, 28)
    random_year = random.randint(2027, 2035)
    booking_date = f"{random_year}-06-{random_day}"
    
    book_res = client.post(
        "/api/v1/queues/book",
        json={"court_id": court_id, "booking_date": booking_date, "time_slot": "10:00-11:00"},
        headers=headers
    )
    assert book_res.status_code == 201
    
    data = book_res.json()
    assert data["member_tier"] == "Standard"
    assert data["fee_to_pay"] == base_price # ราคาเต็ม ไม่ได้ส่วนลด

def test_membership_tier_promotion_flow(client):
    """
    ทดสอบตรรกะคะแนนสะสมและการเลื่อนระดับขั้นสมาชิก (Promotion Flow)
    จำลองการอัปแต้มสะสมโดยตรงและจองสนามเพื่อทดสอบสัดส่วนส่วนลด Silver, Gold, Platinum
    """
    random_id = random.randint(100000, 999999)
    email = f"tier_promo_{random_id}@gmail.com"
    phone = f"087{random_id:07d}"
    
    # 1. สมัครสมาชิกและยืนยันตัวตน
    reg = client.post("/api/v1/auth/register", json={
        "username": f"user_promo_{random_id}",
        "email": email,
        "password": "securepassword123",
        "phone": phone
    })
    user_id = reg.json()["user"]["id"]
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    otp_res = client.post("/api/v1/auth/otp/send", json={"phone": phone})
    otp_code = mock_otp_store[phone]["otp_code"]
    ref_code = mock_otp_store[phone]["ref_code"]
    client.post("/api/v1/auth/otp/verify", json={
        "phone": phone,
        "otp_code": otp_code,
        "ref_code": ref_code
    })
    
    # 2. จำลองการให้แต้มสะสมแก่ผู้ใช้เพื่อเลื่อนขั้นเป็น Silver (แต้มสะสม 1,000 คะแนนขึ้นไป)
    # 10,000 บาท = 1,000 แต้ม
    async def force_silver_upgrade():
        await DataService.award_points_to_user(user_id, 10000.0)
        
    asyncio.run(force_silver_upgrade())
    
    # 3. ลองส่งคำขอจองสนามเพื่อเช็กส่วนลด Silver (ส่วนลด 5%)
    courts_res = client.get("/api/v1/courts?date=2026-06-01")
    court_id = courts_res.json()[0]["id"]
    base_price = courts_res.json()[0]["price_per_hour"]
    
    # ใช้วัน/ปีที่แตกต่างกันอย่างสิ้นเชิงเพื่อป้องกันการชนกัน (Conflict 409) บน Supabase Cloud
    random_day = random.randint(1, 28)
    random_year = random.randint(2040, 2050)
    booking_date = f"{random_year}-07-{random_day}"
    
    book_silver = client.post(
        "/api/v1/queues/book",
        json={"court_id": court_id, "booking_date": booking_date, "time_slot": "10:00-11:00"},
        headers=headers
    )
    assert book_silver.status_code == 201
    assert book_silver.json()["member_tier"] == "Silver"
    assert book_silver.json()["fee_to_pay"] == base_price * 0.95 # ลด 5%
    
    # 4. จำลองการให้แต้มเพิ่มเติมเพื่อเลื่อนขั้นเป็น Gold (แต้มสะสม 5,000 คะแนนขึ้นไป)
    # เพิ่มอีก 40,000 บาท
    async def force_gold_upgrade():
        await DataService.award_points_to_user(user_id, 40000.0)
        
    asyncio.run(force_gold_upgrade())
    
    booking_date_gold = f"{random_year}-07-{random_day + 1 if random_day < 28 else random_day - 1}"
    book_gold = client.post(
        "/api/v1/queues/book",
        json={"court_id": court_id, "booking_date": booking_date_gold, "time_slot": "10:00-11:00"},
        headers=headers
    )
    assert book_gold.status_code == 201
    assert book_gold.json()["member_tier"] == "Gold"
    assert book_gold.json()["fee_to_pay"] == base_price * 0.90 # ลด 10%


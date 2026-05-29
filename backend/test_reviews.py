import pytest
import random
from fastapi.testclient import TestClient
from main import app
from app.services.otp_store import otp_store as mock_otp_store

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_user_review_guards(client):
    """
    ทดสอบระบบความปลอดภัยและ Validations ของ UGC Reviews
    - รีวิว Match ที่ไม่มีอยู่จริง (404)
    - รีวิวตนเอง (400)
    """
    random_id = random.randint(100000, 999999)
    email_a = f"reviewer_a_{random_id}@gmail.com"
    phone_a = f"087{random_id:07d}"
    
    # 1. สมัครและยืนยันตัวตนผู้ใช้ A
    client.post("/api/v1/auth/register", json={
        "username": f"user_a_{random_id}",
        "email": email_a,
        "password": "securepassword123",
        "phone": phone_a
    })
    
    otp_send_a = client.post("/api/v1/auth/otp/send", json={"phone": phone_a})
    otp_entry_a = mock_otp_store[phone_a]
    client.post("/api/v1/auth/otp/verify", json={
        "phone": phone_a,
        "otp_code": otp_entry_a["otp_code"],
        "ref_code": otp_entry_a["ref_code"]
    })
    
    login_a = client.post("/api/v1/auth/login", json={"email": email_a, "password": "securepassword123"})
    token_a = login_a.json()["access_token"]
    user_a_id = login_a.json()["user"]["id"]
    headers_a = {"Authorization": f"Bearer {token_a}"}
    
    # 2. ทดสอบรีวิวแมตช์ที่ไม่มีอยู่จริง (404)
    res_404 = client.post(
        "/api/v1/matches/non-existent-match-id/reviews",
        json={"reviewee_id": "some-user-id", "rating": 5, "comment": "Good play"},
        headers=headers_a
    )
    assert res_404.status_code == 404
    
    # 3. ทดสอบการรีวิวตนเอง (400)
    # สมัครคอร์ทและตั้งค่า Match เพื่อให้ผ่านข้อแรก
    courts_res = client.get("/api/v1/courts?date=2026-06-01")
    court_id = courts_res.json()[0]["id"]
    
    match_res = client.post(
        "/api/v1/matching/find",
        json={
            "court_id": court_id,
            "match_date": "2026-06-01",
            "time_slot": "18:00-19:00",
            "match_type": "singles",
            "ntrp_min": 1.5,
            "ntrp_max": 5.0
        },
        headers=headers_a
    )
    assert match_res.status_code == 200
    match_id = match_res.json()["match_id"]
    
    res_self = client.post(
        f"/api/v1/matches/{match_id}/reviews",
        json={"reviewee_id": user_a_id, "rating": 5, "comment": "Self rating!"},
        headers=headers_a
    )
    assert res_self.status_code == 400
    assert "รีวิวหรือให้คะแนนดาวตัวเองได้" in res_self.json()["detail"]

def test_user_review_calculation_and_success_flow(client):
    """
    ทดสอบการส่งรีวิวให้ผู้ใช้อื่นสำเร็จ และการประมวลผลดาวสะสมเฉลี่ยในโปรไฟล์ได้ถูกต้องแม่นยำ
    """
    random_id = random.randint(100000, 999999)
    
    # 1. สร้างผู้ใช้ A (ผู้รีวิว)
    email_a = f"rev_a_{random_id}@gmail.com"
    phone_a = f"087{random_id:07d}"
    client.post("/api/v1/auth/register", json={
        "username": f"rev_user_a_{random_id}",
        "email": email_a,
        "password": "securepassword123",
        "phone": phone_a
    })
    otp_send_a = client.post("/api/v1/auth/otp/send", json={"phone": phone_a})
    otp_entry_a = mock_otp_store[phone_a]
    client.post("/api/v1/auth/otp/verify", json={
        "phone": phone_a,
        "otp_code": otp_entry_a["otp_code"],
        "ref_code": otp_entry_a["ref_code"]
    })
    login_a = client.post("/api/v1/auth/login", json={"email": email_a, "password": "securepassword123"})
    token_a = login_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}
    
    # 2. สร้างผู้ใช้ B (ผู้ถูกรีวิว)
    email_b = f"rev_b_{random_id}@gmail.com"
    phone_b = f"0871{random_id:06d}"
    reg_b = client.post("/api/v1/auth/register", json={
        "username": f"rev_user_b_{random_id}",
        "email": email_b,
        "password": "securepassword123",
        "phone": phone_b
    })
    user_b_id = reg_b.json()["user"]["id"]
    
    otp_send_b = client.post("/api/v1/auth/otp/send", json={"phone": phone_b})
    otp_entry_b = mock_otp_store[phone_b]
    client.post("/api/v1/auth/otp/verify", json={
        "phone": phone_b,
        "otp_code": otp_entry_b["otp_code"],
        "ref_code": otp_entry_b["ref_code"]
    })
    
    # 3. ผู้ใช้ A โพสต์จัดตั้งแมตช์
    courts_res = client.get("/api/v1/courts?date=2026-06-01")
    court_id = courts_res.json()[0]["id"]
    match_res = client.post(
        "/api/v1/matching/find",
        json={
            "court_id": court_id,
            "match_date": "2026-06-01",
            "time_slot": "19:00-20:00",
            "match_type": "singles",
            "ntrp_min": 1.5,
            "ntrp_max": 5.0
        },
        headers=headers_a
    )
    match_id = match_res.json()["match_id"]
    
    # หมายเหตุ: จำลองให้ B ร่วมเล่นในแมตช์นั้น โดย Host (A) ส่งรีวิว
    # (ในระบบ MVP ตาราง Match จัดเก็บ host_user_id และเก็บ user อื่นใน invited_user_ids
    # เพื่อความสะดวกในการทดสอบฟลูเวิร์กโฟลว์การอนุญาตของ endpoint ให้เราจำลอง B ใน invited_user_ids)
    from app.services.data_service import AsyncSessionLocal
    from app.models import Match
    from sqlalchemy import select
    
    async def force_add_invited_user():
        async with AsyncSessionLocal() as session:
            stmt = select(Match).where(Match.id == match_id)
            res = await session.execute(stmt)
            m = res.scalars().first()
            if m:
                m.invited_user_ids = [user_b_id]
                await session.commit()
                
    import asyncio
    asyncio.run(force_add_invited_user())
    
    # 4. ผู้ใช้ A ส่งรีวิวให้คะแนนผู้ใช้ B ด้วยคะแนน 4.0 ดาว
    review_res = client.post(
        f"/api/v1/matches/{match_id}/reviews",
        json={"reviewee_id": user_b_id, "rating": 4, "comment": "Good partner"},
        headers=headers_a
    )
    assert review_res.status_code == 201
    
    # 5. ตรวจสอบข้อมูลในฐานข้อมูลโดยตรงสำหรับผู้ใช้ B เพื่อดูว่าคะแนนสะสมเฉลี่ยถูกคำนวณและอัปเดตอย่างสมบูรณ์แบบ
    from app.services.data_service import DataService
    async def get_updated_user_profile():
        u = await DataService.get_user_by_id(user_b_id)
        return u["profile"] if u else {}
        
    user_b_profile = asyncio.run(get_updated_user_profile())
    
    assert user_b_profile.get("rating_average") == 4.0
    assert user_b_profile.get("rating_count") == 1

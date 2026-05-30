import pytest
import random
from fastapi.testclient import TestClient
from main import app
from app.services.otp_store import otp_store as mock_otp_store

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def get_unique_user_payload(base_username: str):
    num = random.randint(1000000, 9999999)
    return {
        "username": f"{base_username}_{num}",
        "email": f"{base_username}_{num}@hotmail.com",
        "password": "supersecurepassword123",
        "phone": f"087{num:07d}"
    }

def test_voucher_system_flow(client):
    # 1. Register a test player
    payload = get_unique_user_payload("voucher_player")
    email = payload["email"]
    phone = payload["phone"]
    
    print(f"\n[TEST] 1. Registering test player: {email}...")
    register_response = client.post("/api/v1/auth/register", json=payload)
    assert register_response.status_code == 201
    user_data = register_response.json()
    user_id = user_data["user"]["id"]
    token = user_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 📞 Bypass phone OTP to allow booking
    otp_response = client.post("/api/v1/auth/otp/send", json={"phone": phone})
    assert otp_response.status_code == 200
    otp_entry = mock_otp_store[phone]
    verify_response = client.post("/api/v1/auth/otp/verify", json={
        "phone": phone,
        "otp_code": otp_entry["otp_code"],
        "ref_code": otp_entry["ref_code"]
    })
    assert verify_response.status_code == 200

    # 2. Seed test vouchers into database
    import asyncio
    async def seed_vouchers():
        from app.services.data_service import DataService
        # fixed discount 100 Baht
        await DataService.create_voucher(
            code="WELCOME100",
            discount_type="fixed",
            discount_value=100.0,
            min_booking_amount=200.0,
            max_uses=5,
            is_active=True
        )
        # percentage discount 10%
        await DataService.create_voucher(
            code="TENNIS10",
            discount_type="percentage",
            discount_value=10.0,
            min_booking_amount=300.0,
            max_discount=50.0,
            max_uses=10,
            is_active=True
        )
        # expired voucher
        await DataService.create_voucher(
            code="EXPIRED50",
            discount_type="fixed",
            discount_value=50.0,
            expiry_date="2020-01-01",
            is_active=True
        )
        
    asyncio.run(seed_vouchers())
    print("[TEST] 2. Seeded WELCOME100, TENNIS10, and EXPIRED50 vouchers successfully")

    # 3. Grab first court ID
    courts_response = client.get("/api/v1/courts?date=2026-06-28")
    assert courts_response.status_code == 200
    court_id = courts_response.json()[0]["id"]

    # 4. Try booking with EXPIRED50 (should fail)
    print("[TEST] 3. Booking with expired promo code (should raise 400)...")
    expired_payload = {
        "court_id": court_id,
        "booking_date": "2026-06-28",
        "time_slot": "10:00-11:00",
        "promo_code": "EXPIRED50"
    }
    exp_response = client.post("/api/v1/queues/book", json=expired_payload, headers=headers)
    assert exp_response.status_code == 400
    assert "หมดอายุ" in exp_response.json()["detail"]

    # 5. Book successfully with WELCOME100 (fixed discount)
    print("[TEST] 4. Booking successfully applying fixed discount WELCOME100...")
    valid_payload = {
        "court_id": court_id,
        "booking_date": "2026-06-28",
        "time_slot": "10:00-11:00",
        "promo_code": "WELCOME100"
    }
    book_response = client.post("/api/v1/queues/book", json=valid_payload, headers=headers)
    assert book_response.status_code == 201
    book_data = book_response.json()
    assert book_data["promo_discount"] == 100.0
    assert book_data["fee_to_pay"] == book_data["member_price"] - 100.0
    booking_id = book_data["booking_id"]
    
    # 6. Verify one-time use constraint (user attempts to reuse WELCOME100)
    print("[TEST] 5. Verifying double-usage protection guard (should raise 400)...")
    reuse_payload = {
        "court_id": court_id,
        "booking_date": "2026-06-28",
        "time_slot": "11:00-12:00",
        "promo_code": "WELCOME100"
    }
    reuse_response = client.post("/api/v1/queues/book", json=reuse_payload, headers=headers)
    assert reuse_response.status_code == 400
    assert "ใช้งานรหัสส่วนลดพิเศษนี้ไปแล้ว" in reuse_response.json()["detail"]

    # Cleanup DB
    async def cleanup():
        from app.services.data_service import AsyncSessionLocal
        from app.models import User, Booking, UserVoucher, Voucher
        from sqlalchemy import delete
        
        async with AsyncSessionLocal() as session:
            await session.execute(delete(UserVoucher).where(UserVoucher.user_id == user_id))
            await session.execute(delete(Booking).where(Booking.id == booking_id))
            await session.execute(delete(User).where(User.id == user_id))
            await session.execute(delete(Voucher).where(Voucher.code.in_(["WELCOME100", "TENNIS10", "EXPIRED50"])))
            await session.commit()
            
    asyncio.run(cleanup())
    print("[TEST] SUCCESS - Voucher Redeem System Phase 3 flows verified successfully!")

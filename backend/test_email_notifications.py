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

def test_email_notifications_flow(client):
    # 1. 👥 POST /auth/register -> Triggers Welcome Email
    payload = get_unique_user_payload("test_player")
    email = payload["email"]
    phone = payload["phone"]
    
    print(f"\n[TEST] 1. Registering user {email} (should trigger Welcome Email)...")
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == email
    
    token = data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 📞 POST /auth/otp/send & verify to clear phone check
    otp_response = client.post("/api/v1/auth/otp/send", json={"phone": phone})
    assert otp_response.status_code == 200
    otp_entry = mock_otp_store[phone]
    otp_code = otp_entry["otp_code"]
    ref_code = otp_entry["ref_code"]
    
    verify_response = client.post("/api/v1/auth/otp/verify", json={
        "phone": phone,
        "otp_code": otp_code,
        "ref_code": ref_code
    })
    assert verify_response.status_code == 200

    # 📅 GET /courts to grab first court ID
    courts_response = client.get(f"/api/v1/courts?date=2026-06-25")
    assert courts_response.status_code == 200
    courts_data = courts_response.json()
    court_id = courts_data[0]["id"]
    
    # 2. 📅 POST /queues/book -> Triggers Awaiting Payment Email
    booking_payload = {
        "court_id": court_id,
        "booking_date": "2026-06-25",
        "time_slot": "10:00-11:00"
    }
    print(f"[TEST] 2. Booking court (should trigger Awaiting Payment Email)...")
    book_response = client.post("/api/v1/queues/book", json=booking_payload, headers=headers)
    assert book_response.status_code == 201
    book_data = book_response.json()
    assert book_data["status"] == "pending_payment"
    booking_id = book_data["booking_id"]
    
    # 3. 💳 POST /payments/pay
    file_content = b"fake-image-bytes"
    files = {"slip_file": ("slip.png", file_content, "image/png")}
    form_data = {"booking_id": booking_id, "amount": 500.0}
    pay_response = client.post("/api/v1/payments/pay", data=form_data, files=files, headers=headers)
    assert pay_response.status_code == 200
    tx_id = pay_response.json()["transaction_id"]
    
    # 4. 👑 Admin: Approve Payment -> Triggers Booking Confirmed Email
    admin_login = {
        "email": "managingdirector@kfd.co.th",
        "password": "securepassword123"
    }
    admin_auth = client.post("/api/v1/auth/login", json=admin_login)
    assert admin_auth.status_code == 200
    admin_token = admin_auth.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    verify_payload = {"action": "approve", "note": "Approved!"}
    print(f"[TEST] 3. Approving payment (should trigger Booking Confirmed Email)...")
    verify_tx_response = client.patch(f"/api/v1/admin/payments/{tx_id}/verify", json=verify_payload, headers=admin_headers)
    assert verify_tx_response.status_code == 200
    
    # Cleanup DB
    import asyncio
    async def cleanup():
        from app.services.data_service import AsyncSessionLocal
        from app.models import User, Booking, Transaction
        from sqlalchemy import delete
        
        async with AsyncSessionLocal() as session:
            await session.execute(delete(Transaction).where(Transaction.id == tx_id))
            await session.execute(delete(Booking).where(Booking.id == booking_id))
            await session.execute(delete(User).where(User.id == data["user"]["id"]))
            await session.commit()
            
    asyncio.run(cleanup())
    print("[TEST] SUCCESS - Email Notification flow tested without errors!")

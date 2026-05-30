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
        "email": f"{base_username}_{num}@example.com",
        "password": "supersecurepassword123",
        "phone": f"087{num}"
    }

def test_full_player_workflow(client):
    # 1. 👥 POST /auth/register
    payload = get_unique_user_payload("test_player")
    email = payload["email"]
    phone = payload["phone"]
    
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == email
    assert data["user"]["is_phone_verified"] is False
    
    token = data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. 📞 POST /auth/otp/send
    otp_response = client.post("/api/v1/auth/otp/send", json={"phone": phone})
    assert otp_response.status_code == 200
    otp_data = otp_response.json()
    assert "ref_code" in otp_data
    
    # Fetch generated OTP from simulator mock_otp_store
    otp_entry = mock_otp_store[phone]
    otp_code = otp_entry["otp_code"]
    ref_code = otp_entry["ref_code"]
    
    # 📞 POST /auth/otp/verify
    verify_response = client.post("/api/v1/auth/otp/verify", json={
        "phone": phone,
        "otp_code": otp_code,
        "ref_code": ref_code
    })
    assert verify_response.status_code == 200
    
    # 3. 📅 GET /courts with randomized booking date to prevent 409 slot conflict across test runs
    random_day = random.randint(10, 28)
    random_year = random.randint(2027, 2035)
    booking_date = f"{random_year}-06-{random_day}"
    
    courts_response = client.get(f"/api/v1/courts?date={booking_date}")
    assert courts_response.status_code == 200
    courts_data = courts_response.json()
    assert len(courts_data) >= 2
    court_1_id = courts_data[0]["id"]
    
    # 4. 📅 POST /queues/book
    booking_payload = {
        "court_id": court_1_id,
        "booking_date": booking_date,
        "time_slot": "16:00-17:00"
    }
    book_response = client.post("/api/v1/queues/book", json=booking_payload, headers=headers)
    assert book_response.status_code == 201
    book_data = book_response.json()
    assert book_data["status"] == "pending_payment"
    booking_id = book_data["booking_id"]
    
    # Check duplicate booking guard (raises 409 Conflict because the slot is already busy)
    dup_response = client.post("/api/v1/queues/book", json=booking_payload, headers=headers)
    assert dup_response.status_code == 409
    
    # 5. 💳 POST /payments/pay (Upload slip)
    # Simulate a file upload
    file_content = b"fake-image-bytes"
    files = {"slip_file": ("slip.png", file_content, "image/png")}
    form_data = {"booking_id": booking_id, "amount": 500.0}
    
    pay_response = client.post("/api/v1/payments/pay", data=form_data, files=files, headers=headers)
    assert pay_response.status_code == 200
    pay_data = pay_response.json()
    assert pay_data["status"] == "processing"
    tx_id = pay_data["transaction_id"]
    
    # 6. 👑 Admin: GET /admin/payments/pending
    # First, authenticate as Admin
    admin_login = {
        "email": "managingdirector@kfd.co.th",
        "password": "securepassword123"
    }
    admin_auth = client.post("/api/v1/auth/login", json=admin_login)
    assert admin_auth.status_code == 200
    admin_token = admin_auth.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    pending_response = client.get("/api/v1/admin/payments/pending", headers=admin_headers)
    assert pending_response.status_code == 200
    pending_txs = pending_response.json()
    # Ensure our transaction is in the list
    assert any(tx["transaction_id"] == tx_id for tx in pending_txs)
    
    # 7. 👑 Admin: PATCH /admin/payments/{tx_id}/verify (Approve)
    verify_payload = {"action": "approve", "note": "Verified!"}
    verify_tx_response = client.patch(f"/api/v1/admin/payments/{tx_id}/verify", json=verify_payload, headers=admin_headers)
    assert verify_tx_response.status_code == 200
    assert verify_tx_response.json()["transaction_status"] == "verified"
    
    # Verify booking status is now confirmed
    my_bookings = client.get("/api/v1/queues", headers=headers)
    assert my_bookings.status_code == 200
    assert any(b["booking_id"] == booking_id and b["status"] == "confirmed" for b in my_bookings.json())

    # Cleanup DB to keep Supabase clean
    import asyncio
    async def cleanup():
        from app.services.data_service import AsyncSessionLocal
        from app.models import User, Booking, Transaction
        # pyrefly: ignore [missing-import]
        from sqlalchemy import delete
        
        async with AsyncSessionLocal() as session:
            await session.execute(delete(Transaction).where(Transaction.id == tx_id))
            await session.execute(delete(Booking).where(Booking.id == booking_id))
            await session.execute(delete(User).where(User.id == data["user"]["id"]))
            await session.commit()
            
    asyncio.run(cleanup())

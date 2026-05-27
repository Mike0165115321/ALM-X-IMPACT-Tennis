import pytest
from fastapi.testclient import TestClient
from main import app
from app.services.mock_db import mock_users, mock_otp_store, mock_bookings, mock_transactions

client = TestClient(app)

def test_full_player_workflow():
    # 1. 👥 POST /auth/register
    email = "test_player@example.com"
    register_payload = {
        "username": "test_player",
        "email": email,
        "password": "supersecurepassword123",
        "phone": "0877777777"
    }
    
    response = client.post("/api/v1/auth/register", json=register_payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == email
    assert data["user"]["is_phone_verified"] is False
    
    token = data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. 📞 POST /auth/otp/send
    otp_response = client.post("/api/v1/auth/otp/send", json={"phone": "0877777777"})
    assert otp_response.status_code == 200
    otp_data = otp_response.json()
    assert "ref_code" in otp_data
    
    # Fetch generated OTP from simulator mock_otp_store
    otp_entry = mock_otp_store["0877777777"]
    otp_code = otp_entry["otp_code"]
    ref_code = otp_entry["ref_code"]
    
    # 📞 POST /auth/otp/verify
    verify_response = client.post("/api/v1/auth/otp/verify", json={
        "phone": "0877777777",
        "otp_code": otp_code,
        "ref_code": ref_code
    })
    assert verify_response.status_code == 200
    
    # 3. 📅 GET /courts
    courts_response = client.get("/api/v1/courts?date=2026-05-30")
    assert courts_response.status_code == 200
    courts_data = courts_response.json()
    assert len(courts_data) >= 2
    court_1_id = courts_data[0]["id"]
    
    # 4. 📅 POST /queues/book
    booking_payload = {
        "court_id": court_1_id,
        "booking_date": "2026-05-30",
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
        "email": "admin@impacttennis.com",
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

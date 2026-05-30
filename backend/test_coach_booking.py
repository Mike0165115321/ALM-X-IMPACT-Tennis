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

def test_coach_booking_flow(client):
    # 1. Register a user
    payload = get_unique_user_payload("test_player")
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    user_data = response.json()
    token = user_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Get coaches (triggers auto-seeding)
    print("\n[TEST] 1. Listing coaches...")
    coaches_response = client.get("/api/v1/coaches", headers=headers)
    assert coaches_response.status_code == 200
    coaches = coaches_response.json()
    assert len(coaches) >= 2
    
    # Select first coach and an available slot
    coach = coaches[0]
    coach_id = coach["id"]
    free_slot = next((s for s in coach.get("available_slots", []) if not s.get("is_booked")), None)
    if not free_slot:
        free_slot = coach["available_slots"][0]
    time_slot = free_slot["time_slot"]
    booking_date = "2026-06-20"
    
    # 3. Book coach
    book_payload = {
        "coach_id": coach_id,
        "booking_date": booking_date,
        "time_slot": time_slot
    }
    print(f"[TEST] 2. Booking coach {coach_id} for slot {time_slot}...")
    book_response = client.post("/api/v1/coaches/book", json=book_payload, headers=headers)
    assert book_response.status_code == 201
    book_data = book_response.json()
    assert book_data["status"] == "pending_payment"
    booking_id = book_data["booking_id"]
    
    # 4. Check duplicate slot conflict
    print("[TEST] 3. Verifying double booking conflict guard works...")
    dup_response = client.post("/api/v1/coaches/book", json=book_payload, headers=headers)
    assert dup_response.status_code == 409
    
    # 5. List user coach bookings
    print("[TEST] 4. Listing user's coach booking history...")
    history_response = client.get("/api/v1/coaches/bookings", headers=headers)
    assert history_response.status_code == 200
    bookings = history_response.json()
    assert any(b["id"] == booking_id for b in bookings)
    
    # Cleanup DB
    import asyncio
    async def cleanup():
        from app.services.data_service import AsyncSessionLocal
        from app.models import User, CoachBooking
        from sqlalchemy import delete
        
        async with AsyncSessionLocal() as session:
            await session.execute(delete(CoachBooking).where(CoachBooking.id == booking_id))
            await session.execute(delete(User).where(User.id == user_data["user"]["id"]))
            await session.commit()
            
    asyncio.run(cleanup())
    print("[TEST] SUCCESS - Coach booking flow tested successfully without errors!")

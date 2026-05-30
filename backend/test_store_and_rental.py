import pytest
import random
from fastapi.testclient import TestClient
from main import app

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

def test_store_and_rental_flow(client):
    # 1. Register a user
    payload = get_unique_user_payload("test_player")
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    user_data = response.json()
    token = user_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Get store items (triggers auto-seeding)
    print("\n[TEST] 1. Listing store items...")
    store_response = client.get("/api/v1/store/items", headers=headers)
    assert store_response.status_code == 200
    items = store_response.json()
    assert len(items) >= 3
    
    # Find Water and Racket rental IDs and save initial water stock
    water_id = None
    racket_id = None
    water_initial_stock = 0
    
    for item in items:
        if "Water" in item["item_name"]:
            water_id = item["id"]
            water_initial_stock = item["stock_quantity"]
        elif "Racket" in item["item_name"]:
            racket_id = item["id"]
            
    assert water_id is not None
    assert racket_id is not None
    
    # 3. Create store order (Buy water, rent racket)
    order_payload = {
        "items": [
            {"item_id": water_id, "quantity": 3},
            {"item_id": racket_id, "quantity": 1}
        ]
    }
    print(f"[TEST] 2. Ordering water (x3) and racket rental (x1)...")
    order_response = client.post("/api/v1/store/orders", json=order_payload, headers=headers)
    assert order_response.status_code == 201
    order_data = order_response.json()
    assert order_data["status"] == "pending_payment"
    order_id = order_data["order_id"]
    
    # 4. Check stock decremented
    print("[TEST] 3. Verifying stock was updated...")
    store_response_after = client.get("/api/v1/store/items", headers=headers)
    items_after = store_response_after.json()
    
    for item in items_after:
        if item["id"] == water_id:
            # should have decremented by 3
            assert item["stock_quantity"] == water_initial_stock - 3
            
    # 5. List user orders
    print("[TEST] 4. Listing user's order history...")
    history_response = client.get("/api/v1/store/orders", headers=headers)
    assert history_response.status_code == 200
    orders = history_response.json()
    assert any(o["id"] == order_id for o in orders)
    
    # Cleanup DB
    import asyncio
    async def cleanup():
        from app.services.data_service import AsyncSessionLocal
        from app.models import User, Order, Merchandise
        from sqlalchemy import delete
        
        async with AsyncSessionLocal() as session:
            await session.execute(delete(Order).where(Order.id == order_id))
            await session.execute(delete(User).where(User.id == user_data["user"]["id"]))
            # Restore stock
            await session.commit()
            
    asyncio.run(cleanup())
    print("[TEST] SUCCESS - Storefront & Equipment Rental flow tested successfully without errors!")

import pytest
import random
from fastapi.testclient import TestClient
from main import app

def test_hotmail_register_and_login():
    client = TestClient(app)
    
    # 1. สุ่มอีเมล Hotmail เพื่อป้องกันการสมัครซ้ำในการรันเทส
    random_num = random.randint(1000000, 9999999) # สุ่ม 7 หลัก
    test_email = f"tennis_fan_{random_num}@hotmail.com"
    test_password = "securePassword123!"
    test_phone = f"087{random_num:07d}" # ให้ได้เบอร์โทรศัพท์ 10 หลักครบถ้วน (เช่น 0871234567)
    test_username = f"hotmail_player_{random_num}"
    
    # 2. ทดสอบสมัครสมาชิก (Register) ด้วยอีเมล Hotmail
    register_payload = {
        "username": test_username,
        "email": test_email,
        "password": test_password,
        "phone": test_phone
    }
    
    print(f"\n[TEST] 1. Starting registration with Hotmail email: {test_email}...")
    register_response = client.post("/api/v1/auth/register", json=register_payload)
    
    assert register_response.status_code == 201, f"Register failed: {register_response.text}"
    register_data = register_response.json()
    assert register_data["user"]["email"] == test_email
    print(f"[TEST] SUCCESS - Registered Hotmail User with ID: {register_data['user']['id']}")
    
    # 3. ทดสอบเข้าสู่ระบบ (Login) ด้วยอีเมล Hotmail และรหัสผ่านที่สมัครไว้
    login_payload = {
        "email": test_email,
        "password": test_password
    }
    
    print(f"[TEST] 2. Starting login with Hotmail email: {test_email}...")
    login_response = client.post("/api/v1/auth/login", json=login_payload)
    
    assert login_response.status_code == 200, f"Login failed: {login_response.text}"
    login_data = login_response.json()
    assert "access_token" in login_data
    assert login_data["user"]["email"] == test_email
    print(f"[TEST] SUCCESS - Logged in with Hotmail! Access token obtained.")
    
    # 4. ลบข้อมูลผู้ใช้ทดสอบออกจาก Supabase DB เพื่อความสะอาดเรียบร้อย
    import asyncio
    async def cleanup():
        from app.services.data_service import AsyncSessionLocal
        from app.models import User
        # pyrefly: ignore [missing-import]
        from sqlalchemy import delete
        
        async with AsyncSessionLocal() as session:
            stmt = delete(User).where(User.email == test_email)
            await session.execute(stmt)
            await session.commit()
        print(f"[TEST] CLEANUP - Deleted test user: {test_email} from Supabase")
        
    asyncio.run(cleanup())

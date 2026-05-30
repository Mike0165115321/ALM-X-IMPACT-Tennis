import pytest
import os
from fastapi.testclient import TestClient
from main import app
from app.config import settings

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_easyslip_connection_direct(client):
    """
    ทดสอบการเชื่อมต่อ API ของ EasySlip v2 โดยตรงผ่าน API Key จริง
    จุดนี้จะยิงคำขอของจริง เพื่อให้ตัวเลข Request ในแดชบอร์ด EasySlip ของพี่เด้งขึ้น!
    """
    print(f"\n[TEST] [LINK] Connecting to EasySlip with Key: {settings.EASYSLIP_API_KEY[:8]}...")
    
    # 1. ยิงเรียก GET /info ของ EasySlip
    import httpx
    headers = {
        "Authorization": f"Bearer {settings.EASYSLIP_API_KEY}"
    }
    
    response = httpx.get("https://api.easyslip.com/v2/info", headers=headers, timeout=10.0)
    print(f"[TEST] [STATUS] EasySlip Response Status: {response.status_code}")
    
    # ถ้า Key ถูกต้องและงานใช้งานได้จริง ควรจะตอบกลับมาเป็น 200 OK
    assert response.status_code == 200
    res_data = response.json()
    assert res_data.get("success") is True
    print(f"[TEST] [SUCCESS] Connect Success: {res_data['data']}")

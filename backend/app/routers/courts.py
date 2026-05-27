from fastapi import APIRouter, Query, HTTPException, status
from typing import List, Dict, Any
from datetime import datetime

from app.services.mock_db import mock_courts, mock_bookings
from app.services.data_service import DataService

router = APIRouter(prefix="/api/v1/courts", tags=["Courts"])

@router.get("")
def list_courts(date: str = Query(None, description="วันที่ต้องการจอง ฟอร์แมต YYYY-MM-DD (เช่น 2026-05-27) ค่าเริ่มต้นคือวันนี้")):
    if not date:
        date = datetime.utcnow().strftime("%Y-%m-%d")
        
    try:
        # ตรวจสอบฟอร์แมตวันที่เบื้องต้น
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="รูปแบบวันที่ไม่ถูกต้อง กรุณาใช้ YYYY-MM-DD"
        )
        
    result = []
    for court_id, court in mock_courts.items():
        court_copy = {
            "id": court["id"],
            "court_name": court["court_name"],
            "location": court["location"],
            "price_per_hour": court["price_per_hour"],
            "available_slots": []
        }
        
        # สำหรับแต่ละ slot ในสล็อตที่มี ให้ประเมินความพร้อมแบบ Dynamic อ้างอิงจาก mock_bookings
        for slot in court["available_slots"]:
            time_slot = slot["time_slot"]
            # ตรวจสอบว่าในวันที่กำหนด มีคนจองและยืนยัน/อยู่ระหว่างดำเนินการในระบบแล้วหรือไม่
            is_booked = DataService.is_slot_booked(court_id, date, time_slot)
            
            court_copy["available_slots"].append({
                "time_slot": time_slot,
                "is_booked": is_booked
            })
            
        result.append(court_copy)
        
    return result

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Any

from app.services.data_service import DataService
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/v1/queues", tags=["Queue & Booking"])

# ----------------- Pydantic Request Models -----------------

class BookRequest(BaseModel):
    court_id: str
    booking_date: str  # YYYY-MM-DD
    time_slot: str     # เช่น "18:00-20:00"

# ----------------- Route Endpoints -----------------

@router.get("")
def get_queues(current_user: Dict[str, Any] = Depends(get_current_user)):
    # ถ้าเป็น admin ให้แสดงข้อมูลทั้งหมด ถ้าเป็นผู้เล่นทั่วไป ให้แสดงเฉพาะคิวของตัวเอง
    if current_user["role"] == "admin":
        return DataService.get_all_bookings()
    else:
        return DataService.get_bookings_by_user(current_user["id"])

@router.post("/book", status_code=status.HTTP_201_CREATED)
def book_court(payload: BookRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    # ตรวจสอบเบอร์โทรศัพท์ว่าทำการยืนยันตัวตน OTP หรือยัง ตามความปลอดภัย
    if not current_user["profile"]["is_phone_verified"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="กรุณายืนยันเบอร์โทรศัพท์ด้วย OTP ก่อนจองสนาม"
        )
        
    booking = DataService.create_booking(
        user_id=current_user["id"],
        court_id=payload.court_id,
        booking_date=payload.booking_date,
        time_slot=payload.time_slot
    )
    
    return {
        "message": "Booking request created successfully",
        "booking_id": booking["id"],
        "status": booking["status"]
    }

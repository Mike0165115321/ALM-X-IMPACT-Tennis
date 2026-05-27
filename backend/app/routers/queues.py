from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime

from app.services.data_service import DataService
from app.services.mock_db import mock_courts
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
        
    # 1. ตรวจสอบว่ามีสนามนี้ในระบบจริงหรือไม่
    if payload.court_id not in mock_courts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ไม่พบสนามที่ระบุในระบบ"
        )
        
    # 2. ตรวจสอบรูปแบบวันที่เบื้องต้น
    try:
        datetime.strptime(payload.booking_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="รูปแบบวันที่ไม่ถูกต้อง กรุณาใช้ YYYY-MM-DD"
        )

    # 3. ตรวจสอบว่าเวลานี้ถูกจองไปแล้วหรือยัง (Slot Conflict Guard)
    if DataService.is_slot_booked(payload.court_id, payload.booking_date, payload.time_slot):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="สล็อตเวลานี้ในสนามดังกล่าวถูกจองเต็มแล้ว"
        )
        
    # 4. ตรวจสอบว่าผู้ใช้คนนี้จองสล็อตนี้ซ้ำไปแล้วหรือยัง (Duplicate Booking Guard)
    if DataService.has_user_booked_slot(current_user["id"], payload.booking_date, payload.time_slot):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="คุณจองสนามในสล็อตเวลานี้ไปแล้ว"
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

@router.patch("/{booking_id}/cancel")
def cancel_booking(booking_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    booking = DataService.get_booking_by_id(booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ไม่พบรายการจองนี้ในระบบ"
        )
        
    # ผู้เล่นที่ไม่ใช่อักษรย่อ admin สามารถยกเลิกได้เฉพาะการจองของตนเอง
    if current_user["role"] != "admin" and booking["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="คุณไม่มีสิทธิ์ยกเลิกการจองของผู้อื่น"
        )
        
    # สามารถยกเลิกได้เฉพาะตอนที่ยังไม่ได้ตรวจสอบสลิป หรือรอการโอนเงิน (pending_payment หรือ pending_verification หรือ payment_rejected)
    if booking["status"] not in ["pending_payment", "pending_verification", "payment_rejected"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"ไม่สามารถยกเลิกการจองที่มีสถานะ {booking['status']} ได้"
        )
        
    updated_booking = DataService.cancel_booking(booking_id)
    return {
        "message": "Booking cancelled successfully",
        "booking_id": updated_booking["id"],
        "status": updated_booking["status"]
    }

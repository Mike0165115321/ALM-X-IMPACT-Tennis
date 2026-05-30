from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Any

from app.services.data_service import DataService
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/v1/coaches", tags=["Coaches & Academy (Phase 2)"])

class CoachBookRequest(BaseModel):
    coach_id: str
    booking_date: str # YYYY-MM-DD
    time_slot: str # "09:00-10:00"

@router.get("", response_model=List[Dict[str, Any]])
async def list_coaches(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    ดึงรายชื่อผู้สอน/โค้ชทั้งหมดพร้อมตารางสอนที่ว่าง
    """
    return await DataService.get_all_coaches()

@router.post("/book", status_code=status.HTTP_201_CREATED)
async def book_coach(payload: CoachBookRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    ทำรายการจองชั่วโมงสอนของโค้ช
    """
    # 1. ตรวจสอบว่ามีโค้ชคนนี้ในระบบจริงหรือไม่
    coach = await DataService.get_coach_by_id(payload.coach_id)
    if not coach:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ไม่พบโค้ชหรือผู้สอนที่ระบุในระบบ"
        )
        
    # 2. ตรวจสอบเบื้องต้นว่ามีสล็อตนี้ในตารางทำงานของโค้ชหรือไม่ และสว่างจริงหรือไม่
    slot_exists = False
    for slot in coach.get("available_slots", []):
        if slot["time_slot"] == payload.time_slot:
            slot_exists = True
            if slot["is_booked"]:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="ขออภัย สล็อตเวลานี้ของโค้ชได้รับการจองไปเรียบร้อยแล้ว"
                )
            break
            
    if not slot_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ขออภัย ไม่พบสล็อตเวลาทำงานนี้ในตารางประวัติของโค้ชคนดังกล่าว"
        )

    # 3. เช็คความขัดแย้งเวลาในตารางจองจริง (Double check in DB)
    if await DataService.is_coach_slot_booked(payload.coach_id, payload.booking_date, payload.time_slot):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="ขออภัย สล็อตเวลาสอนนี้ของโค้ชถูกผู้ใช้อื่นทำรายการจองไปเรียบร้อยแล้ว"
        )

    # 4. บันทึกการจองและปรับสถานะสล็อต
    try:
        booking = await DataService.create_coach_booking(
            user_id=current_user["id"],
            coach_id=payload.coach_id,
            booking_date=payload.booking_date,
            time_slot=payload.time_slot
        )
        return {
            "message": "Coach booking request created successfully",
            "booking_id": booking["id"],
            "status": booking["status"],
            "price": coach["price_per_hour"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"เกิดข้อผิดพลาดในการประมวลผลการจองโค้ช: {str(e)}"
        )

@router.get("/bookings", response_model=List[Dict[str, Any]])
async def list_user_coach_bookings(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    ดึงรายการประวัติการจองโค้ชของผู้เล่นแต่ละราย
    """
    return await DataService.get_coach_bookings_by_user(current_user["id"])

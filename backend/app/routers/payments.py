from fastapi import APIRouter, Depends, UploadFile, File, Form, Request, HTTPException, status
from typing import Dict, Any

from app.services.data_service import DataService
from app.services.storage_service import StorageService
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/v1/payments", tags=["Payments"])

# ----------------- Route Endpoints -----------------

@router.post("/pay")
async def upload_payment_slip(
    request: Request,
    booking_id: str = Form(...),
    amount: float = Form(...),
    slip_file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    # 1. ตรวจสอบรายการจองและความเป็นเจ้าของก่อนทำธุรกรรม (M6)
    booking = await DataService.get_booking_by_id(booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ไม่พบรายการจองนี้ในระบบ"
        )
        
    if booking["user_id"] != current_user["id"] and current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="คุณไม่มีสิทธิ์อัปโหลดสลิปชำระเงินสำหรับรายการจองของผู้อื่น"
        )
        
    # ส่งต่อให้ StorageService จัดการการเก็บไฟล์ ตรวจสอบประเภทไฟล์ และสร้าง URL จริง
    slip_url = await StorageService.upload_slip(slip_file, booking_id, request)
    
    tx = await DataService.create_transaction(
        user_id=current_user["id"],
        booking_id=booking_id,
        amount=amount,
        payment_method="BankTransfer",
        slip_url=slip_url
    )
    
    return {
        "transaction_id": tx["id"],
        "status": tx["status"],
        "message": "อัปโหลดรูปภาพสลิปโอนเงินเรียบร้อยแล้ว รอการอนุมัติจากแอดมิน",
        "slip_url": slip_url
    }

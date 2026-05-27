from fastapi import APIRouter, Depends, UploadFile, File, Form, Request
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
    # ส่งต่อให้ StorageService จัดการการเก็บไฟล์ ตรวจสอบประเภทไฟล์ และสร้าง URL จริง
    slip_url = StorageService.upload_slip(slip_file, booking_id, request)
    
    tx = DataService.create_transaction(
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



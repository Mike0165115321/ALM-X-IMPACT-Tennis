from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import Dict, Any

from app.services.data_service import DataService
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/v1/payments", tags=["Payments"])

# ----------------- Route Endpoints -----------------

@router.post("/pay")
async def upload_payment_slip(
    booking_id: str = Form(...),
    amount: float = Form(...),
    slip_file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    # ตรวจสอบประเภทไฟล์ของภาพสลิปเบื้องต้น
    if not slip_file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="กรุณาอัปโหลดไฟล์รูปภาพสลิปที่ถูกต้อง (PNG, JPG, JPEG, WEBP)"
        )
        
    # ในสภาวะจำลอง เราจะบันทึก Slip URL เป็นตำแหน่งพอร์ตจำลอง
    slip_url_simulated = f"https://storage.googleapis.com/alm-tennis-slips/{slip_file.filename}"
    
    tx = DataService.create_transaction(
        user_id=current_user["id"],
        booking_id=booking_id,
        amount=amount,
        payment_method="BankTransfer",
        slip_url=slip_url_simulated
    )
    
    return {
        "transaction_id": tx["id"],
        "status": tx["status"],
        "message": "Payment slip uploaded, waiting for verification"
    }

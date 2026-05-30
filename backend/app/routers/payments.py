from fastapi import APIRouter, Depends, UploadFile, File, Form, Request, HTTPException, status
from typing import Dict, Any
import os

from app.services.data_service import DataService
from app.services.storage_service import StorageService
from app.services.qr_decoder import QRDecoder
from app.services.easyslip_service import EasySlipService
from app.config import settings
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
            status_code=status.HTTP_430_FORBIDDEN if hasattr(status, "HTTP_430_FORBIDDEN") else 403,
            detail="คุณไม่มีสิทธิ์อัปโหลดสลิปชำระเงินสำหรับรายการจองของผู้อื่น"
        )
        
    # ส่งต่อให้ StorageService จัดการการเก็บไฟล์ ตรวจสอบประเภทไฟล์ และสร้าง URL จริง
    slip_url = await StorageService.upload_slip(slip_file, booking_id, request)
    
    # ดึง Local file path เพื่อส่งไปถอดรหัส QR Payload
    filename = slip_url.split("/")[-1]
    local_file_path = os.path.join(StorageService.UPLOAD_DIR, filename)
    
    # 2. ถอดรหัส QR Code (Mini-QR) จากสลิป
    qr_payload = QRDecoder.decode_qr(local_file_path)
    
    auto_verified = False
    verification_message = "อัปโหลดรูปภาพสลิปโอนเงินเรียบร้อยแล้ว รอการอนุมัติจากแอดมิน"
    
    # 3. หากดึง QR Payload สำเร็จ และมี API Key ให้เช็ก EasySlip อัตโนมัติทันที
    if qr_payload and settings.EASYSLIP_API_KEY:
        verify_res = await EasySlipService.verify_slip(
            api_key=settings.EASYSLIP_API_KEY,
            qr_payload=qr_payload,
            expected_amount=amount
        )
        
        # หากสลิปได้รับการยืนยันและยอดเงินถูกต้องจริง
        if verify_res.get("success") is True and verify_res.get("is_amount_matched") is True:
            auto_verified = True
            verification_message = "🎉 สลิปโอนเงินได้รับการยืนยันความถูกต้องผ่านระบบอัตโนมัติเรียบร้อย! คิวจองของคุณยืนยัน (Confirmed) ทันที!"
            
    # 4. บันทึกธุรกรรมลงในตาราง
    tx = await DataService.create_transaction(
        user_id=current_user["id"],
        booking_id=booking_id,
        amount=amount,
        payment_method="BankTransfer",
        slip_url=slip_url
    )
    
    # 5. หากยืนยันอัตโนมัติผ่าน ปรับสถานะธุรกรรมและการจองคิวเป็นสำเร็จทันทีโดยไม่ต้องรอแอดมิน!
    if auto_verified:
        await DataService.verify_payment(tx["id"], "approve")
        # โหลดธุรกรรมเวอร์ชันอัปเดตเพื่อส่งกลับ
        updated_tx = await DataService.get_transaction_by_id(tx["id"])
        tx_status = updated_tx["status"] if updated_tx else "verified"
    else:
        tx_status = tx["status"]
    
    return {
        "transaction_id": tx["id"],
        "status": tx_status,
        "auto_verified": auto_verified,
        "message": verification_message,
        "slip_url": slip_url
    }

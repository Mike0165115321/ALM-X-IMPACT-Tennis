from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any

from app.services.data_service import DataService
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/v1/admin", tags=["Admin (Management)"])

# ----------------- Pydantic Request Models -----------------

class VerifyPaymentRequest(BaseModel):
    action: str = Field(..., description="การดำเนินการ: 'approve' (อนุมัติสลิป) หรือ 'reject' (ปฏิเสธสลิป)")
    note: str = Field("", description="บันทึกเพิ่มเติมหรือเหตุผลการปฏิเสธ")

# ----------------- Helper Role Guard -----------------

def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ขออภัย เฉพาะผู้ดูแลระบบ (Admin) เท่านั้นที่เข้าถึงฟังก์ชันนี้ได้"
        )
    return current_user

# ----------------- Route Endpoints -----------------

@router.get("/payments/pending", response_model=List[Dict[str, Any]])
def list_pending_payments(admin_user: Dict[str, Any] = Depends(require_admin)):
    """
    ดึงรายการสลิปชำระเงินทั้งหมดที่รอการตรวจสอบ (status = 'processing')
    """
    return DataService.get_pending_transactions()

@router.patch("/payments/{transaction_id}/verify")
def verify_payment(
    transaction_id: str,
    payload: VerifyPaymentRequest,
    admin_user: Dict[str, Any] = Depends(require_admin)
):
    """
    อนุมัติหรือปฏิเสธภาพสลิปชำระเงินโอน
    - 'approve': ปรับสถานะธุรกรรมเป็น 'verified' และจองคิวสนามเป็น 'confirmed'
    - 'reject': ปรับสถานะธุรกรรมเป็น 'failed' และจองคิวสนามเป็น 'payment_rejected'
    """
    if payload.action not in ["approve", "reject"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="การดำเนินการไม่ถูกต้อง ต้องระบุเป็น 'approve' หรือ 'reject'"
        )
        
    tx = DataService.get_transaction_by_id(transaction_id)
    if not tx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ไม่พบธุรกรรมหรือสลิปชำระเงินที่ระบุในระบบ"
        )
        
    updated_tx = DataService.verify_payment(transaction_id, payload.action)
    
    return {
        "message": f"Payment successfully {payload.action}d",
        "transaction_id": updated_tx["id"],
        "transaction_status": updated_tx["status"],
        "booking_id": updated_tx["booking_id"]
    }

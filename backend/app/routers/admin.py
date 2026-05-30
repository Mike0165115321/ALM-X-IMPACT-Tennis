from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Any

from app.services.data_service import DataService
from app.services.email_service import EmailService
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/v1/admin", tags=["Admin (Management)"])

# ----------------- Pydantic Request Models -----------------

class VerifyPaymentRequest(BaseModel):
    action: str = Field(..., description="การดำเนินการ: 'approve' (อนุมัติสลิป) หรือ 'reject' (ปฏิเสธสลิป)")
    note: str = Field("", description="บันทึกเพิ่มเติมหรือเหตุผลการปฏิเสธ")

# ----------------- Helper Role Guard -----------------

async def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ขออภัย เฉพาะผู้ดูแลระบบ (Admin) เท่านั้นที่เข้าถึงฟังก์ชันนี้ได้"
        )
    return current_user

# ----------------- Route Endpoints -----------------

@router.get("/payments/pending", response_model=List[Dict[str, Any]])
async def list_pending_payments(admin_user: Dict[str, Any] = Depends(require_admin)):
    """
    ดึงรายการสลิปชำระเงินทั้งหมดที่รอการตรวจสอบ (status = 'processing')
    """
    return await DataService.get_pending_transactions()

@router.patch("/payments/{transaction_id}/verify")
async def verify_payment(
    transaction_id: str,
    payload: VerifyPaymentRequest,
    background_tasks: BackgroundTasks,
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
        
    tx = await DataService.get_transaction_by_id(transaction_id)
    if not tx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ไม่พบธุรกรรมหรือสลิปชำระเงินที่ระบุในระบบ"
        )
        
    updated_tx = await DataService.verify_payment(transaction_id, payload.action)
    
    # 🎖️ เมื่อสลิปผ่านการอนุมัติจริง (approve) ให้ทำการให้แต้มสมาชิกและส่งอีเมลแจ้งเตือน
    if payload.action == "approve" and updated_tx:
        user_id = updated_tx.get("user_id")
        amount = updated_tx.get("amount", 0.0)
        if user_id and amount > 0:
            await DataService.award_points_to_user(user_id, amount)
            
        # ดึงข้อมูลเพิ่มเติมเพื่อมาประกอบเนื้อหาอีเมลยืนยันการจองคอร์ทสำเร็จ
        user = await DataService.get_user_by_id(user_id)
        booking = await DataService.get_booking_by_id(updated_tx["booking_id"])
        if user and booking:
            court = await DataService.get_court_by_id(booking["court_id"])
            court_name = court.get("court_name", "Court Room") if court else "Impact Tennis Court"
            
            confirm_html = f"""
            <html>
              <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <h2 style="color: #2f855a;">ยินดีด้วย! การชำระเงินค่าจองคอร์ทสำเร็จเรียบร้อย 🎉</h2>
                <p>สวัสดีคุณ {user['username']},</p>
                <p>ทีมงานแอดมินได้ตรวจสอบหลักฐานสลิปการโอนเงินจำนวน <b>{updated_tx['amount']} บาท</b> ของคุณเสร็จสมบูรณ์เรียบร้อยแล้ว รายการจองของคุณได้รับการยืนยัน (Confirmed) เรียบร้อย!</p>
                
                <table style="border-collapse: collapse; width: 100%; margin: 15px 0;">
                  <tr style="background-color: #f7fafc;">
                    <td style="padding: 8px; border: 1px solid #e2e8f0; font-weight: bold;">สนาม</td>
                    <td style="padding: 8px; border: 1px solid #e2e8f0;">{court_name}</td>
                  </tr>
                  <tr>
                    <td style="padding: 8px; border: 1px solid #e2e8f0; font-weight: bold;">วันที่จอง</td>
                    <td style="padding: 8px; border: 1px solid #e2e8f0;">{booking['booking_date']}</td>
                  </tr>
                  <tr style="background-color: #f7fafc;">
                    <td style="padding: 8px; border: 1px solid #e2e8f0; font-weight: bold;">ช่วงเวลา</td>
                    <td style="padding: 8px; border: 1px solid #e2e8f0;">{booking['time_slot']}</td>
                  </tr>
                  <tr>
                    <td style="padding: 8px; border: 1px solid #e2e8f0; font-weight: bold;">รหัสรายการจอง</td>
                    <td style="padding: 8px; border: 1px solid #e2e8f0; font-family: monospace; color: #d53f8c;">{booking['id']}</td>
                  </tr>
                </table>
                
                <p style="background-color: #ebf8ff; border-left: 4px solid #3182ce; padding: 12px;">
                  <b>💡 คำแนะนำ:</b> กรุณาเซฟหน้าจออีเมลฉบับนี้ หรือจดรหัสรายการจอง เพื่อนำไปแสดงให้กับเจ้าหน้าที่ที่เคาน์เตอร์สโมสรในวันที่เข้าใช้บริการสนามครับ
                </p>
                <p>ขอให้สนุกกับแมตช์เทนนิสและการหาคู่ตีที่เต็มไปด้วยคุณภาพนะครับ!</p>
                <br/>
                <p>ขอแสดงความนับถือ,<br/><b>ทีมงาน ALMxIMPACT Tennis Club</b></p>
              </body>
            </html>
            """
            background_tasks.add_task(
                EmailService.send_email,
                user["email"],
                "ใบยืนยันการจองคอร์ทเทนนิสสำเร็จ (Confirmed) ALMxIMPACT 🎾🏆",
                confirm_html
            )
            
    return {
        "message": f"Payment successfully {payload.action}d",
        "transaction_id": updated_tx["id"],
        "transaction_status": updated_tx["status"],
        "booking_id": updated_tx["booking_id"]
    }

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.services.data_service import DataService
from app.services.email_service import EmailService
from app.routers.auth import get_current_user
from app.exceptions import SlotConflictException, UserDuplicateBookingException

router = APIRouter(prefix="/api/v1/queues", tags=["Queue & Booking"])

# ----------------- Pydantic Request Models -----------------

class BookRequest(BaseModel):
    court_id: str
    booking_date: str  # YYYY-MM-DD
    time_slot: str     # เช่น "18:00-20:00"
    promo_code: Optional[str] = None # รหัสคูปองส่วนลดสะสม (ถ้ามี)

# ----------------- Route Endpoints -----------------

@router.get("")
async def get_queues(current_user: Dict[str, Any] = Depends(get_current_user)):
    # ถ้าเป็น admin ให้แสดงข้อมูลทั้งหมด ถ้าเป็นผู้เล่นทั่วไป ให้แสดงเฉพาะคิวของตัวเอง
    if current_user["role"] == "admin":
        return await DataService.get_all_bookings()
    else:
        return await DataService.get_bookings_by_user(current_user["id"])

@router.post("/book", status_code=status.HTTP_201_CREATED)
async def book_court(
    payload: BookRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    # ตรวจสอบเบอร์โทรศัพท์ว่าทำการยืนยันตัวตน OTP หรือยัง ตามความปลอดภัย
    if not current_user["profile"]["is_phone_verified"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="กรุณายืนยันเบอร์โทรศัพท์ด้วย OTP ก่อนจองสนาม"
        )
        
    # 1. ตรวจสอบว่ามีสนามนี้ในระบบจริงหรือไม่ ผ่าน DataService เท่านั้น
    if not await DataService.get_court_by_id(payload.court_id):
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
    if await DataService.is_slot_booked(payload.court_id, payload.booking_date, payload.time_slot):
        raise SlotConflictException()
        
    # 4. ตรวจสอบว่าผู้ใช้คนนี้จองสล็อตนี้ซ้ำไปแล้วหรือยัง (Duplicate Booking Guard)
    if await DataService.has_user_booked_slot(current_user["id"], payload.booking_date, payload.time_slot):
        raise UserDuplicateBookingException()
        
    # 5. ดึงข้อมูลอัตราค่าบริการของสนามและประมวลผลราคาพิเศษตามระดับสมาชิก
    court = await DataService.get_court_by_id(payload.court_id)
    base_price = court.get("price_per_hour", 500.0) if court else 500.0
    discounted_price = await DataService.get_discounted_price_for_user(current_user["id"], base_price)
    
    # 6. ตรวจสอบรหัสส่วนลดคูปองเพิ่มเติม (Voucher Redeem)
    promo_discount = 0.0
    applied_code = None
    if payload.promo_code:
        try:
            applied_code = payload.promo_code.upper().strip()
            promo_discount = await DataService.validate_and_apply_voucher(
                current_user["id"],
                applied_code,
                discounted_price
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
            
    fee_to_pay = max(0.0, discounted_price - promo_discount)

    # 7. สร้างรายการจองสนามพร้อมแนบรายละเอียดส่วนลดคูปอง
    booking = await DataService.create_booking(
        user_id=current_user["id"],
        court_id=payload.court_id,
        booking_date=payload.booking_date,
        time_slot=payload.time_slot,
        applied_voucher_code=applied_code,
        discount_amount=promo_discount
    )
    
    # 8. ส่งอีเมลสรุปข้อมูลการจองและแจ้งยอดโอนชำระเงิน
    court_name = court.get("court_name", "Court Room") if court else "Impact Tennis Court"
    
    voucher_row = ""
    if promo_discount > 0.0:
        voucher_row = f"""
          <tr style="background-color: #e6fffa; color: #0d9488;">
            <td style="padding: 8px; border: 1px solid #cbd5e0; font-weight: bold;">ส่วนลดคูปอง ({applied_code})</td>
            <td style="padding: 8px; border: 1px solid #cbd5e0; font-weight: bold;">- {promo_discount} บาท</td>
          </tr>
        """
        
    payment_html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h2 style="color: #2b6cb0;">ใบแจ้งสรุปการจองสนามเทนนิส 🎾 (รอกระบวนการโอนชำระเงิน)</h2>
        <p>สวัสดีคุณ {current_user['username']},</p>
        <p>เราได้รับคำขอจองคิวสนามของคุณเรียบร้อยแล้ว โดยมีรายละเอียดดังนี้:</p>
        <table style="border-collapse: collapse; width: 100%; margin: 15px 0;">
          <tr style="background-color: #f7fafc;">
            <td style="padding: 8px; border: 1px solid #e2e8f0; font-weight: bold;">สนาม</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">{court_name}</td>
          </tr>
          <tr>
            <td style="padding: 8px; border: 1px solid #e2e8f0; font-weight: bold;">วันที่จอง</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">{payload.booking_date}</td>
          </tr>
          <tr style="background-color: #f7fafc;">
            <td style="padding: 8px; border: 1px solid #e2e8f0; font-weight: bold;">ช่วงเวลา</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">{payload.time_slot}</td>
          </tr>
          <tr>
            <td style="padding: 8px; border: 1px solid #e2e8f0; font-weight: bold;">ค่าสนามปกติ</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">{base_price} บาท</td>
          </tr>
          <tr style="background-color: #edf2f7; font-weight: bold; color: #2d3748;">
            <td style="padding: 8px; border: 1px solid #cbd5e0;">ราคาส่วนลดของคุณ ({current_user['profile'].get('member_tier', 'Standard')})</td>
            <td style="padding: 8px; border: 1px solid #cbd5e0;">{discounted_price} บาท</td>
          </tr>
          {voucher_row}
          <tr style="background-color: #edf2f7; font-weight: bold; color: #1a202c; font-size: 1.1em;">
            <td style="padding: 8px; border: 1px solid #cbd5e0;">ยอดโอนชำระเงินสุทธิ</td>
            <td style="padding: 8px; border: 1px solid #cbd5e0; font-weight: bold; color: #e53e3e;">{fee_to_pay} บาท</td>
          </tr>
        </table>
        
        <div style="background-color: #fffaf0; border-left: 4px solid #dd6b20; padding: 15px; margin: 15px 0;">
          <h4 style="margin: 0 0 8px 0; color: #dd6b20;">📌 ขั้นตอนการโอนเงินเพื่อยืนยันสิทธิ์จองคอร์ท:</h4>
          <p style="margin: 0;">กรุณาโอนเงินจำนวน <b>{fee_to_pay} บาท</b> ไปยังธนาคารกสิกรไทย (KBANK)<br/>
          เลขที่บัญชี: <b>999-9-99999-9</b> (ชื่อบัญชี: บจก. เคเอฟยู)<br/>
          เมื่อโอนเสร็จแล้ว รบอนุมัติแนบหลักฐานสลิปโอนเงินผ่านระบบหน้าเว็บเพื่อยืนยันสิทธิ์ทันทีครับ!</p>
        </div>
        <p>ขอบคุณที่ใช้บริการ,<br/><b>ทีมงาน ALMxIMPACT Tennis Club</b></p>
      </body>
    </html>
    """
    background_tasks.add_task(
        EmailService.send_email,
        current_user["email"],
        "ใบสรุปยอดโอนเงินค่าจองคอร์ทเทนนิส ALMxIMPACT 🎾",
        payment_html
    )
    
    return {
        "message": "Booking request created successfully",
        "booking_id": booking["id"],
        "status": booking["status"],
        "base_price": base_price,
        "member_price": discounted_price,
        "promo_discount": promo_discount,
        "fee_to_pay": fee_to_pay,
        "member_tier": current_user["profile"].get("member_tier", "Standard"),
        "applied_promo_code": applied_code
    }

@router.patch("/{booking_id}/cancel")
async def cancel_booking(booking_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    booking = await DataService.get_booking_by_id(booking_id)
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
        
    updated_booking = await DataService.cancel_booking(booking_id)
    return {
        "message": "Booking cancelled successfully",
        "booking_id": updated_booking["id"],
        "status": updated_booking["status"]
    }

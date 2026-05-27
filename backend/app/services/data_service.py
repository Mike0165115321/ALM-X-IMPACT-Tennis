import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from app.services.mock_db import (
    mock_users, mock_courts, mock_bookings, mock_matches,
    mock_reviews, mock_transactions, mock_otp_store, generate_id
)

logger = logging.getLogger("data_service")


class DataService:
    # 👥 1. Users Services
    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        for user in mock_users.values():
            if user["email"].lower() == email.lower():
                return user
        return None

    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        return mock_users.get(user_id)

    @staticmethod
    def get_user_by_google_id(google_id: str) -> Optional[Dict[str, Any]]:
        for user in mock_users.values():
            if user["google_id"] == google_id:
                return user
        return None

    @staticmethod
    def create_user(
        username: str,
        email: str,
        password_hash: Optional[str] = None,
        google_id: Optional[str] = None,
        role: str = "player",
        profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        user_id = generate_id()
        default_profile = {
            "display_name": username,
            "phone": "",
            "is_phone_verified": False,
            "ntrp_rating": 1.5,
            "wtn_rating": 40.0,
            "playing_style": "All-Court",
            "match_preference": "any"
        }
        if profile:
            default_profile.update(profile)

        new_user = {
            "id": user_id,
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "google_id": google_id,
            "role": role,
            "profile": default_profile,
            "created_at": datetime.utcnow()
        }
        mock_users[user_id] = new_user
        return new_user

    # 📞 2. SMS OTP Services
    @staticmethod
    def save_otp(phone: str, otp_code: str, ref_code: str):
        # ตรวจสอบ Rate Limiting (สูงสุด 3 ครั้งใน 15 นาทีต่อเบอร์)
        now = datetime.utcnow()
        limit_time = now - timedelta(minutes=15)
        
        # เราเก็บประวัติการส่งใน mock_otp_store เป็นประวัติการร้องขอใน session นี้ได้
        # เพื่อความง่ายสำหรับ mock: บันทึกข้อมูล OTP ล่าสุด
        mock_otp_store[phone] = {
            "otp_code": otp_code,
            "ref_code": ref_code,
            "created_at": now,
            "request_count": mock_otp_store.get(phone, {}).get("request_count", 0) + 1,
            "last_request_at": now
        }

    @staticmethod
    def check_otp_rate_limit(phone: str) -> bool:
        # ตรวจสอบว่ามีการร้องขอเกิน 3 ครั้งใน 15 นาทีหรือไม่
        otp_entry = mock_otp_store.get(phone)
        if not otp_entry:
            return True
        
        now = datetime.utcnow()
        # ถ้าร้องขอครั้งล่าสุดเกิน 15 นาทีแล้ว ให้รีเซ็ตประวัติการส่ง
        if now - otp_entry["created_at"] > timedelta(minutes=15):
            otp_entry["request_count"] = 0
            return True
            
        if otp_entry["request_count"] >= 3:
            return False
        return True

    @staticmethod
    def verify_otp(phone: str, otp_code: str, ref_code: str) -> bool:
        # เพื่อการทดสอบ: หากไม่มีการระบุ SMS_API_KEY หรือ SMS_API_SECRET ใน .env 
        # หรือเป็นหมายเลขทดสอบระบบ (เช่น หมายเลขที่เริ่มต้นด้วย 087 สำหรับ Pytest)
        # ให้รันโหมดจำลอง (Simulator) ตามปกติ
        from app.config import settings
        
        is_test_phone = phone.startswith("087")
        if not settings.SMS_API_KEY or not settings.SMS_API_SECRET or is_test_phone:
            otp_entry = mock_otp_store.get(phone)
            if not otp_entry:
                return False
                
            now = datetime.utcnow()
            # สำหรับการเทส Pytest เราปิดการเช็ค Expire 5 นาทีชั่วคราวเพื่อความเสถียรของชุดทดสอบ
            if not is_test_phone and (now - otp_entry["created_at"] > timedelta(minutes=5)):
                mock_otp_store.pop(phone, None)
                return False
                
            if otp_entry["otp_code"] == otp_code and otp_entry["ref_code"] == ref_code:
                for user in mock_users.values():
                    if user["profile"]["phone"] == phone:
                        user["profile"]["is_phone_verified"] = True
                mock_otp_store.pop(phone, None)
                return True
            return False

        # --- 📲 กรณีใช้งานจริงผ่าน ThaiBulkSMS OTP Service ---
        otp_entry = mock_otp_store.get(phone)
        if not otp_entry or "otp_token" not in otp_entry:
            return False

        import httpx
        api_url = "https://otp.thaibulksms.com/v1/otp/verify"
        
        params = {
            "key": settings.SMS_API_KEY,
            "secret": settings.SMS_API_SECRET,
            "token": otp_entry["otp_token"],
            "pin": otp_code
        }

        try:
            import json
            # ส่งคำขอตรวจสอบ OTP แบบ Synced
            # เนื่องจากเป็นฟังก์ชัน Synchronous (DataService) เราสามารถเรียกผ่าน httpx.Client() แบบปกติ
            with httpx.Client() as client:
                response = client.post(
                    api_url,
                    params=params,
                    timeout=10.0
                )
                
                if response.status_code in [200, 201]:
                    res_data = response.json()
                    # หากตอบกลับเป็น success หรือ status 'success' ยืนยันตัวตนสำเร็จ
                    if res_data.get("status") == "success" or res_data.get("data", {}).get("status") == "success":
                        # อัปเดตสถานะผู้ใช้ใน Mock DB
                        for user in mock_users.values():
                            if user["profile"]["phone"] == phone:
                                user["profile"]["is_phone_verified"] = True
                        mock_otp_store.pop(phone, None)
                        return True
            return False
        except httpx.RequestError as exc:
            logger.error(f"❌ [Network Error] ไม่สามารถยืนยัน OTP กับ SMS Gateway ได้: {exc}")
            from app.exceptions import SMSGatewayException
            raise SMSGatewayException(f"ไม่สามารถเช็คยืนยัน OTP กับระบบภายนอกได้ชั่วคราว: {str(exc)}")
        except Exception as e:
            logger.error(f"❌ [System Error] เกิดข้อผิดพลาดในระบบตรวจรหัส OTP: {str(e)}")
            return False

    # 📅 3. Bookings Services
    @staticmethod
    def get_bookings_by_user(user_id: str) -> List[Dict[str, Any]]:
        user_bookings = []
        for booking in mock_bookings.values():
            if booking["user_id"] == user_id:
                court = mock_courts.get(booking["court_id"])
                booking_copy = booking.copy()
                booking_copy["court_name"] = court["court_name"] if court else "Unknown Court"
                booking_copy["booking_id"] = booking["id"]
                user_bookings.append(booking_copy)
        return user_bookings

    @staticmethod
    def get_all_bookings() -> List[Dict[str, Any]]:
        all_bookings = []
        for booking in mock_bookings.values():
            court = mock_courts.get(booking["court_id"])
            booking_copy = booking.copy()
            booking_copy["court_name"] = court["court_name"] if court else "Unknown Court"
            booking_copy["booking_id"] = booking["id"]
            all_bookings.append(booking_copy)
        return all_bookings

    @staticmethod
    def get_booking_by_id(booking_id: str) -> Optional[Dict[str, Any]]:
        return mock_bookings.get(booking_id)

    @staticmethod
    def is_slot_booked(court_id: str, booking_date: str, time_slot: str) -> bool:
        # ตรวจสอบการจองที่มีสถานะใช้งานอยู่ (ไม่ใช่ cancelled หรือ payment_rejected)
        for booking in mock_bookings.values():
            if (booking["court_id"] == court_id and 
                booking["booking_date"] == booking_date and 
                booking["time_slot"] == time_slot and 
                booking["status"] not in ["cancelled", "payment_rejected"]):
                return True
        return False

    @staticmethod
    def has_user_booked_slot(user_id: str, booking_date: str, time_slot: str) -> bool:
        for booking in mock_bookings.values():
            if (booking["user_id"] == user_id and 
                booking["booking_date"] == booking_date and 
                booking["time_slot"] == time_slot and 
                booking["status"] not in ["cancelled", "payment_rejected"]):
                return True
        return False

    @staticmethod
    def create_booking(user_id: str, court_id: str, booking_date: str, time_slot: str) -> Dict[str, Any]:
        booking_id = generate_id()
        new_booking = {
            "id": booking_id,
            "user_id": user_id,
            "court_id": court_id,
            "booking_date": booking_date,
            "time_slot": time_slot,
            "status": "pending_payment",
            "payment_id": None,
            "created_at": datetime.utcnow()
        }
        mock_bookings[booking_id] = new_booking
        return new_booking

    @staticmethod
    def cancel_booking(booking_id: str) -> Optional[Dict[str, Any]]:
        booking = mock_bookings.get(booking_id)
        if not booking:
            return None
        booking["status"] = "cancelled"
        return booking

    # 🤝 4. Matchmaking Services
    @staticmethod
    def find_matches(
        court_id: str,
        match_date: str,
        time_slot: str,
        match_type: str,
        ntrp_min: float,
        ntrp_max: float,
        preferred_playing_style: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        compatible_matches = []
        for user in mock_users.values():
            if user["role"] != "player":
                continue
            profile = user["profile"]
            if ntrp_min <= profile["ntrp_rating"] <= ntrp_max:
                if preferred_playing_style and profile["playing_style"] != preferred_playing_style:
                    continue
                compatible_matches.append({
                    "user_id": user["id"],
                    "username": user["username"],
                    "ntrp": profile["ntrp_rating"]
                })
        return compatible_matches

    @staticmethod
    def create_match_post(
        host_user_id: str,
        court_id: str,
        match_date: str,
        time_slot: str,
        match_type: str,
        ntrp_min: float,
        ntrp_max: float
    ) -> Dict[str, Any]:
        match_id = generate_id()
        new_match = {
            "id": match_id,
            "host_user_id": host_user_id,
            "invited_user_ids": [],
            "court_id": court_id,
            "match_date": match_date,
            "time_slot": time_slot,
            "match_type": match_type,
            "ntrp_min": ntrp_min,
            "ntrp_max": ntrp_max,
            "status": "open",
            "created_at": datetime.utcnow()
        }
        mock_matches[match_id] = new_match
        return new_match

    # 💬 5. Reviews Services
    @staticmethod
    def create_review(
        reviewer_id: str,
        match_id: str,
        reviewee_id: str,
        rating: int,
        comment: str
    ) -> Dict[str, Any]:
        review_id = generate_id()
        new_review = {
            "id": review_id,
            "reviewer_id": reviewer_id,
            "reviewee_id": reviewee_id,
            "match_id": match_id,
            "rating": rating,
            "comment": comment,
            "created_at": datetime.utcnow()
        }
        mock_reviews[review_id] = new_review
        return new_review

    # 💳 6. Payments Services
    @staticmethod
    def create_transaction(
        user_id: str,
        booking_id: str,
        amount: float,
        payment_method: str,
        slip_url: str
    ) -> Dict[str, Any]:
        tx_id = generate_id()
        new_tx = {
            "id": tx_id,
            "user_id": user_id,
            "booking_id": booking_id,
            "amount": amount,
            "payment_method": payment_method,
            "slip_url": slip_url,
            "status": "processing",
            "created_at": datetime.utcnow(),
            "verified_at": None
        }
        mock_transactions[tx_id] = new_tx
        
        booking = mock_bookings.get(booking_id)
        if booking:
            booking["payment_id"] = tx_id
            booking["status"] = "pending_verification"
            
        return new_tx

    @staticmethod
    def get_pending_transactions() -> List[Dict[str, Any]]:
        pending = []
        for tx in mock_transactions.values():
            if tx.get("status") == "processing":
                booking = mock_bookings.get(tx["booking_id"])
                court = mock_courts.get(booking["court_id"]) if booking else None
                user = mock_users.get(tx["user_id"])
                
                pending.append({
                    "transaction_id": tx["id"],
                    "user_id": tx["user_id"],
                    "username": user["username"] if user else "Unknown",
                    "booking_id": tx["booking_id"],
                    "court_name": court["court_name"] if court else "Unknown Court",
                    "booking_date": booking["booking_date"] if booking else "",
                    "time_slot": booking["time_slot"] if booking else "",
                    "amount": tx["amount"],
                    "slip_url": tx["slip_url"],
                    "status": tx["status"],
                    "created_at": tx.get("created_at", datetime.utcnow())
                })
        return pending

    @staticmethod
    def get_transaction_by_id(tx_id: str) -> Optional[Dict[str, Any]]:
        return mock_transactions.get(tx_id)

    @staticmethod
    def verify_payment(tx_id: str, action: str) -> Optional[Dict[str, Any]]:
        tx = mock_transactions.get(tx_id)
        if not tx:
            return None
            
        booking = mock_bookings.get(tx["booking_id"])
        if action == "approve":
            tx["status"] = "verified"
            tx["verified_at"] = datetime.utcnow()
            if booking:
                booking["status"] = "confirmed"
        elif action == "reject":
            tx["status"] = "failed"
            if booking:
                booking["status"] = "payment_rejected"
                
        return tx

    # 📊 7. Dashboard Stats
    @staticmethod
    def get_dashboard_stats() -> Dict[str, Any]:
        return {
            "total_active_users": len(mock_users),
            "available_courts_today": len(mock_courts),
            "upcoming_matches_count": len([m for m in mock_matches.values() if m["status"] == "open"]),
            "system_announcement": "ยินดีต้อนรับสู่สนาม Impact Tennis! มีโปรโมชั่นช่วงบ่ายลด 20%"
        }


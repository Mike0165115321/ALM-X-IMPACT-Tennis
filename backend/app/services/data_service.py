from datetime import datetime
from typing import List, Dict, Any, Optional
from app.services.mock_db import (
    mock_users, mock_courts, mock_bookings, mock_matches,
    mock_reviews, mock_transactions, mock_otp_store, generate_id
)

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
        mock_otp_store[phone] = {
            "otp_code": otp_code,
            "ref_code": ref_code,
            "created_at": datetime.utcnow()
        }

    @staticmethod
    def verify_otp(phone: str, otp_code: str, ref_code: str) -> bool:
        otp_entry = mock_otp_store.get(phone)
        if otp_entry and otp_entry["otp_code"] == otp_code and otp_entry["ref_code"] == ref_code:
            # ค้นหาผู้ใช้และบันทึกสถานะ
            for user in mock_users.values():
                if user["profile"]["phone"] == phone:
                    user["profile"]["is_phone_verified"] = True
            # ลบ OTP ทิ้งหลังใช้สำเร็จ
            mock_otp_store.pop(phone, None)
            return True
        return False

    # 📅 3. Bookings Services
    @staticmethod
    def get_bookings_by_user(user_id: str) -> List[Dict[str, Any]]:
        user_bookings = []
        for booking in mock_bookings.values():
            if booking["user_id"] == user_id:
                # เติมชื่อสนามเพื่อแสดงใน Response ตามสัญญา API
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
    def create_booking(user_id: str, court_id: str, booking_date: str, time_slot: str) -> Dict[str, Any]:
        booking_id = generate_id()
        new_booking = {
            "id": booking_id,
            "user_id": user_id,
            "court_id": court_id,
            "booking_date": booking_date,
            "time_slot": time_slot,
            "status": "pending_payment",  # ปรับเป็น pending_payment ตาม API Contract
            "payment_id": None,
            "created_at": datetime.utcnow()
        }
        mock_bookings[booking_id] = new_booking
        
        # ปรับสถานะสล็อตเวลาในสนาม
        court = mock_courts.get(court_id)
        if court:
            for slot in court["available_slots"]:
                if slot["time_slot"] == time_slot:
                    slot["is_booked"] = True
                    
        return new_booking

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
        # ค้นหาผู้เล่นที่ตรงกับเงื่อนไข
        compatible_matches = []
        for user in mock_users.values():
            if user["role"] != "player":
                continue
            profile = user["profile"]
            # กรองตามระดับ NTRP
            if ntrp_min <= profile["ntrp_rating"] <= ntrp_max:
                # กรองตามสไตล์การเล่นถ้ามีการระบุ
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
            "amount": amount,
            "payment_method": payment_method,
            "slip_url": slip_url,
            "status": "processing", # รอตรวจสอบสถานะ
            "verified_at": None
        }
        mock_transactions[tx_id] = new_tx
        
        # เชื่อม transaction_id เข้ากับ booking
        booking = mock_bookings.get(booking_id)
        if booking:
            booking["payment_id"] = tx_id
            booking["status"] = "pending_verification" # อัปเดตสถานะการจอง
            
        return new_tx

    # 📊 7. Dashboard Stats
    @staticmethod
    def get_dashboard_stats() -> Dict[str, Any]:
        return {
            "total_active_users": len(mock_users),
            "available_courts_today": len(mock_courts),
            "upcoming_matches_count": len([m for m in mock_matches.values() if m["status"] == "open"]),
            "system_announcement": "ยินดีต้อนรับสู่สนาม Impact Tennis! มีโปรโมชั่นช่วงบ่ายลด 20%"
        }

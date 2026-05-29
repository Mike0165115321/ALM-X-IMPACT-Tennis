import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from beanie import PydanticObjectId

from app.models import User, Court, Booking, Match, Review, Transaction, UserProfile
from app.services.otp_store import otp_store

logger = logging.getLogger("data_service")

def parse_id(id_val: Any) -> Optional[PydanticObjectId]:
    if not id_val:
        return None
    if isinstance(id_val, PydanticObjectId):
        return id_val
    try:
        return PydanticObjectId(str(id_val))
    except Exception:
        return None

def to_dict(doc: Any) -> Optional[Dict[str, Any]]:
    if not doc:
        return None
    res = doc.model_dump() if hasattr(doc, "model_dump") else doc.dict()
    res["id"] = str(doc.id)
    # Convert all PydanticObjectId values to string
    for k, v in list(res.items()):
        if isinstance(v, PydanticObjectId):
            res[k] = str(v)
        elif isinstance(v, list):
            res[k] = [str(x) if isinstance(x, PydanticObjectId) else x for x in v]
    return res

class DataService:
    # 👥 1. Users Services
    @staticmethod
    async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        if not email:
            return None
        user = await User.find_one({"email": {"$regex": f"^{email}$", "$options": "i"}})
        return to_dict(user)

    @staticmethod
    async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        parsed = parse_id(user_id)
        if not parsed:
            return None
        user = await User.get(parsed)
        return to_dict(user)

    @staticmethod
    async def get_user_by_google_id(google_id: str) -> Optional[Dict[str, Any]]:
        if not google_id:
            return None
        user = await User.find_one(User.google_id == google_id)
        return to_dict(user)

    @staticmethod
    async def link_google_id(user_id: str, google_id: str) -> Optional[Dict[str, Any]]:
        parsed = parse_id(user_id)
        if not parsed:
            return None
        user = await User.get(parsed)
        if not user:
            return None
        user.google_id = google_id
        await user.save()
        return to_dict(user)

    @staticmethod
    async def create_user(
        username: str,
        email: str,
        password_hash: Optional[str] = None,
        google_id: Optional[str] = None,
        role: str = "player",
        profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
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

        new_user = User(
            username=username,
            email=email.lower(),
            password_hash=password_hash,
            google_id=google_id,
            role=role,
            profile=UserProfile(**default_profile)
        )
        await new_user.insert()
        return to_dict(new_user)

    # 📞 2. SMS OTP Services
    @staticmethod
    async def save_otp(phone: str, otp_code: str, ref_code: str):
        now = datetime.now(timezone.utc)
        otp_store[phone] = {
            "otp_code": otp_code,
            "ref_code": ref_code,
            "created_at": now,
            "request_count": otp_store.get(phone, {}).get("request_count", 0) + 1,
            "last_request_at": now
        }

    @staticmethod
    async def check_otp_rate_limit(phone: str) -> bool:
        otp_entry = otp_store.get(phone)
        if not otp_entry:
            return True
        
        now = datetime.now(timezone.utc)
        if now - otp_entry["created_at"] > timedelta(minutes=15):
            otp_entry["request_count"] = 0
            return True
            
        if otp_entry["request_count"] >= 3:
            return False
        return True

    @staticmethod
    async def verify_otp(phone: str, otp_code: str, ref_code: str) -> bool:
        from app.config import settings
        from app.services.sms_service import SMSService
        
        is_test_phone = settings.ENABLE_OTP_BYPASS and phone.startswith("087")
        
        if not settings.SMS_API_KEY or not settings.SMS_API_SECRET or is_test_phone:
            otp_entry = otp_store.get(phone)
            if not otp_entry:
                return False
                
            now = datetime.now(timezone.utc)
            if not is_test_phone and (now - otp_entry["created_at"] > timedelta(minutes=5)):
                otp_store.pop(phone, None)
                return False
                
            if otp_entry["otp_code"] == otp_code and otp_entry["ref_code"] == ref_code:
                user = await User.find_one({"profile.phone": phone})
                if user:
                    user.profile.is_phone_verified = True
                    await user.save()
                otp_store.pop(phone, None)
                return True
            return False

        otp_entry = otp_store.get(phone)
        if not otp_entry or "otp_token" not in otp_entry:
            return False

        is_verified = await SMSService.verify_otp_via_api(
            phone=phone,
            otp_code=otp_code,
            otp_token=otp_entry["otp_token"]
        )

        if is_verified:
            user = await User.find_one({"profile.phone": phone})
            if user:
                user.profile.is_phone_verified = True
                await user.save()
            otp_store.pop(phone, None)
            return True
        return False

    # 🏛️ 2.5 Courts Services
    @staticmethod
    async def get_all_courts() -> List[Dict[str, Any]]:
        courts = await Court.find_all().to_list()
        return [to_dict(c) for c in courts]

    @staticmethod
    async def get_court_by_id(court_id: str) -> Optional[Dict[str, Any]]:
        parsed = parse_id(court_id)
        if not parsed:
            return None
        court = await Court.get(parsed)
        return to_dict(court)

    # 📅 3. Bookings Services
    @staticmethod
    async def get_bookings_by_user(user_id: str) -> List[Dict[str, Any]]:
        parsed_user_id = parse_id(user_id)
        if not parsed_user_id:
            return []
        bookings = await Booking.find(Booking.user_id == parsed_user_id).to_list()
        user_bookings = []
        for booking in bookings:
            court = await Court.get(booking.court_id)
            booking_copy = to_dict(booking)
            booking_copy["court_name"] = court.court_name if court else "Unknown Court"
            booking_copy["booking_id"] = str(booking.id)
            user_bookings.append(booking_copy)
        return user_bookings

    @staticmethod
    async def get_all_bookings() -> List[Dict[str, Any]]:
        bookings = await Booking.find_all().to_list()
        all_bookings = []
        for booking in bookings:
            court = await Court.get(booking.court_id)
            booking_copy = to_dict(booking)
            booking_copy["court_name"] = court.court_name if court else "Unknown Court"
            booking_copy["booking_id"] = str(booking.id)
            all_bookings.append(booking_copy)
        return all_bookings

    @staticmethod
    async def get_booking_by_id(booking_id: str) -> Optional[Dict[str, Any]]:
        parsed = parse_id(booking_id)
        if not parsed:
            return None
        booking = await Booking.get(parsed)
        return to_dict(booking)

    @staticmethod
    async def is_slot_booked(court_id: str, booking_date: str, time_slot: str) -> bool:
        parsed_court_id = parse_id(court_id)
        if not parsed_court_id:
            return False
        booking = await Booking.find_one(
            Booking.court_id == parsed_court_id,
            Booking.booking_date == booking_date,
            Booking.time_slot == time_slot,
            Booking.status != "cancelled",
            Booking.status != "payment_rejected"
        )
        return booking is not None

    @staticmethod
    async def has_user_booked_slot(user_id: str, booking_date: str, time_slot: str) -> bool:
        parsed_user_id = parse_id(user_id)
        if not parsed_user_id:
            return False
        booking = await Booking.find_one(
            Booking.user_id == parsed_user_id,
            Booking.booking_date == booking_date,
            Booking.time_slot == time_slot,
            Booking.status != "cancelled",
            Booking.status != "payment_rejected"
        )
        return booking is not None

    @staticmethod
    async def create_booking(user_id: str, court_id: str, booking_date: str, time_slot: str) -> Dict[str, Any]:
        parsed_user_id = parse_id(user_id)
        parsed_court_id = parse_id(court_id)
        if not parsed_user_id or not parsed_court_id:
            raise ValueError("ID ไม่ถูกต้อง")
            
        new_booking = Booking(
            user_id=parsed_user_id,
            court_id=parsed_court_id,
            booking_date=booking_date,
            time_slot=time_slot,
            status="pending_payment",
            payment_id=None
        )
        await new_booking.insert()
        return to_dict(new_booking)

    @staticmethod
    async def cancel_booking(booking_id: str) -> Optional[Dict[str, Any]]:
        parsed = parse_id(booking_id)
        if not parsed:
            return None
        booking = await Booking.get(parsed)
        if not booking:
            return None
        booking.status = "cancelled"
        await booking.save()
        return to_dict(booking)

    # 🤝 4. Matchmaking Services
    @staticmethod
    async def find_matches(
        court_id: str,
        match_date: str,
        time_slot: str,
        match_type: str,
        ntrp_min: float,
        ntrp_max: float,
        preferred_playing_style: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        query = {
            "role": "player",
            "profile.ntrp_rating": {"$gte": ntrp_min, "$lte": ntrp_max}
        }
        if preferred_playing_style:
            query["profile.playing_style"] = preferred_playing_style
            
        users = await User.find(query).to_list()
        compatible_matches = []
        for user in users:
            compatible_matches.append({
                "user_id": str(user.id),
                "username": user.username,
                "ntrp": user.profile.ntrp_rating
            })
        return compatible_matches

    @staticmethod
    async def create_match_post(
        host_user_id: str,
        court_id: str,
        match_date: str,
        time_slot: str,
        match_type: str,
        ntrp_min: float,
        ntrp_max: float
    ) -> Dict[str, Any]:
        parsed_host_user_id = parse_id(host_user_id)
        parsed_court_id = parse_id(court_id)
        if not parsed_host_user_id or not parsed_court_id:
            raise ValueError("ID ไม่ถูกต้อง")
            
        new_match = Match(
            host_user_id=parsed_host_user_id,
            invited_user_ids=[],
            court_id=parsed_court_id,
            match_date=match_date,
            time_slot=time_slot,
            match_type=match_type,
            ntrp_min=ntrp_min,
            ntrp_max=ntrp_max,
            status="open"
        )
        await new_match.insert()
        return to_dict(new_match)

    # 💬 5. Reviews Services
    @staticmethod
    async def create_review(
        reviewer_id: str,
        match_id: str,
        reviewee_id: str,
        rating: int,
        comment: str
    ) -> Dict[str, Any]:
        parsed_reviewer_id = parse_id(reviewer_id)
        parsed_match_id = parse_id(match_id)
        parsed_reviewee_id = parse_id(reviewee_id)
        if not parsed_reviewer_id or not parsed_match_id or not parsed_reviewee_id:
            raise ValueError("ID ไม่ถูกต้อง")
            
        new_review = Review(
            reviewer_id=parsed_reviewer_id,
            reviewee_id=parsed_reviewee_id,
            match_id=parsed_match_id,
            rating=rating,
            comment=comment
        )
        await new_review.insert()
        return to_dict(new_review)

    # 💳 6. Payments Services
    @staticmethod
    async def create_transaction(
        user_id: str,
        booking_id: str,
        amount: float,
        payment_method: str,
        slip_url: str
    ) -> Dict[str, Any]:
        parsed_user_id = parse_id(user_id)
        parsed_booking_id = parse_id(booking_id)
        if not parsed_user_id or not parsed_booking_id:
            raise ValueError("ID ไม่ถูกต้อง")
            
        new_tx = Transaction(
            user_id=parsed_user_id,
            booking_id=parsed_booking_id,
            amount=amount,
            payment_method=payment_method,
            slip_url=slip_url,
            status="processing",
            verified_at=None
        )
        await new_tx.insert()
        
        booking = await Booking.get(parsed_booking_id)
        if booking:
            booking.payment_id = new_tx.id
            booking.status = "pending_verification"
            await booking.save()
            
        return to_dict(new_tx)

    @staticmethod
    async def get_pending_transactions() -> List[Dict[str, Any]]:
        transactions = await Transaction.find(Transaction.status == "processing").to_list()
        pending = []
        for tx in transactions:
            booking = await Booking.get(tx.booking_id)
            court = await Court.get(booking.court_id) if booking else None
            user = await User.get(tx.user_id)
            
            pending.append({
                "transaction_id": str(tx.id),
                "user_id": str(tx.user_id),
                "username": user.username if user else "Unknown",
                "booking_id": str(tx.booking_id),
                "court_name": court.court_name if court else "Unknown Court",
                "booking_date": booking.booking_date if booking else "",
                "time_slot": booking.time_slot if booking else "",
                "amount": tx.amount,
                "slip_url": tx.slip_url,
                "status": tx.status,
                "created_at": tx.created_at
            })
        return pending

    @staticmethod
    async def get_transaction_by_id(tx_id: str) -> Optional[Dict[str, Any]]:
        parsed = parse_id(tx_id)
        if not parsed:
            return None
        tx = await Transaction.get(parsed)
        return to_dict(tx)

    @staticmethod
    async def verify_payment(tx_id: str, action: str) -> Optional[Dict[str, Any]]:
        parsed = parse_id(tx_id)
        if not parsed:
            return None
        tx = await Transaction.get(parsed)
        if not tx:
            return None
            
        booking = await Booking.get(tx.booking_id)
        if action == "approve":
            tx.status = "verified"
            tx.verified_at = datetime.now(timezone.utc)
            if booking:
                booking.status = "confirmed"
                await booking.save()
        elif action == "reject":
            tx.status = "failed"
            if booking:
                booking.status = "payment_rejected"
                await booking.save()
                
        await tx.save()
        return to_dict(tx)

    # 📊 7. Dashboard Stats
    @staticmethod
    async def get_dashboard_stats() -> Dict[str, Any]:
        user_count = await User.count()
        court_count = await Court.count()
        match_count = await Match.find(Match.status == "open").count()
        return {
            "total_active_users": user_count,
            "available_courts_today": court_count,
            "upcoming_matches_count": match_count,
            "system_announcement": "ยินดีต้อนรับสู่สนาม Impact Tennis! มีโปรโมชั่นช่วงบ่ายลด 20%"
        }

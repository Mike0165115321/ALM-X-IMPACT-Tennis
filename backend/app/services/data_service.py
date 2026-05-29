import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
# pyrefly: ignore [missing-import]
from sqlalchemy import select, func, update, and_, or_

# pyrefly: ignore [missing-import]
from sqlalchemy.pool import NullPool
from app.config import settings
from app.models import User, Court, Booking, Match, Review, Transaction
from app.services.otp_store import otp_store

logger = logging.getLogger("data_service")

# 🔌 ตั้งค่า SQLAlchemy Asynchronous Engine และ Session (ใช้ NullPool เพื่อหลีกเลี่ยงการใช้ connection ร่วมกันแบบผิดพลาดในโหมด Async/pytest)
engine = create_async_engine(settings.SUPABASE_DB_URL, poolclass=NullPool, echo=False)
AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

def to_dict(doc: Any) -> Optional[Dict[str, Any]]:
    if not doc:
        return None
    res = {}
    for col in doc.__class__.__table__.columns:
        res[col.name] = getattr(doc, col.name)
    # รับประกันว่า id จะเป็น String แน่ๆ เผื่อกรณี UUID หรือ Types อื่นๆ
    res["id"] = str(doc.id)
    return res

class DataService:
    # 👥 1. Users Services
    @staticmethod
    async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        if not email:
            return None
        async with AsyncSessionLocal() as session:
            stmt = select(User).where(func.lower(User.email) == email.lower().strip())
            res = await session.execute(stmt)
            user = res.scalars().first()
            return to_dict(user)

    @staticmethod
    async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        if not user_id:
            return None
        async with AsyncSessionLocal() as session:
            stmt = select(User).where(User.id == str(user_id))
            res = await session.execute(stmt)
            user = res.scalars().first()
            return to_dict(user)

    @staticmethod
    async def get_user_by_google_id(google_id: str) -> Optional[Dict[str, Any]]:
        if not google_id:
            return None
        async with AsyncSessionLocal() as session:
            stmt = select(User).where(User.google_id == google_id)
            res = await session.execute(stmt)
            user = res.scalars().first()
            return to_dict(user)

    @staticmethod
    async def link_google_id(user_id: str, google_id: str) -> Optional[Dict[str, Any]]:
        if not user_id:
            return None
        async with AsyncSessionLocal() as session:
            stmt = select(User).where(User.id == str(user_id))
            res = await session.execute(stmt)
            user = res.scalars().first()
            if not user:
                return None
            user.google_id = google_id
            await session.commit()
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

        async with AsyncSessionLocal() as session:
            new_user = User(
                id=str(uuid.uuid4()),
                username=username,
                email=email.lower().strip(),
                password_hash=password_hash,
                google_id=google_id,
                role=role,
                profile=default_profile,
                created_at=datetime.now(timezone.utc)
            )
            session.add(new_user)
            await session.commit()
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
                # ค้นหาผู้ใช้และอัปเดตเบอร์โทรเป็นยืนยันแล้ว
                async with AsyncSessionLocal() as session:
                    # ใน PostgreSQL คอลัมน์ profile เป็น JSONB สามารถตรวจสอบฟิลด์ nested ได้
                    stmt = select(User).where(User.profile['phone'].as_string() == phone)
                    res = await session.execute(stmt)
                    user = res.scalars().first()
                    if user:
                        # อัปเดตแบบ Deep copy ของ JSON dict เพื่อบังคับ SQLAlchemy ตรวจจับความเปลี่ยนแปลง
                        updated_profile = dict(user.profile)
                        updated_profile["is_phone_verified"] = True
                        user.profile = updated_profile
                        await session.commit()
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
            async with AsyncSessionLocal() as session:
                stmt = select(User).where(User.profile['phone'].as_string() == phone)
                res = await session.execute(stmt)
                user = res.scalars().first()
                if user:
                    updated_profile = dict(user.profile)
                    updated_profile["is_phone_verified"] = True
                    user.profile = updated_profile
                    await session.commit()
            otp_store.pop(phone, None)
            return True
        return False

    # 🏛️ 2.5 Courts Services
    @staticmethod
    async def get_all_courts() -> List[Dict[str, Any]]:
        async with AsyncSessionLocal() as session:
            stmt = select(Court)
            res = await session.execute(stmt)
            courts = res.scalars().all()
            return [to_dict(c) for c in courts]

    @staticmethod
    async def get_court_by_id(court_id: str) -> Optional[Dict[str, Any]]:
        if not court_id:
            return None
        async with AsyncSessionLocal() as session:
            stmt = select(Court).where(Court.id == str(court_id))
            res = await session.execute(stmt)
            court = res.scalars().first()
            return to_dict(court)

    # 📅 3. Bookings Services
    @staticmethod
    async def get_bookings_by_user(user_id: str) -> List[Dict[str, Any]]:
        if not user_id:
            return []
        async with AsyncSessionLocal() as session:
            stmt = select(Booking).where(Booking.user_id == str(user_id))
            res = await session.execute(stmt)
            bookings = res.scalars().all()
            
            user_bookings = []
            for booking in bookings:
                court_stmt = select(Court).where(Court.id == booking.court_id)
                court_res = await session.execute(court_stmt)
                court = court_res.scalars().first()
                
                booking_copy = to_dict(booking)
                booking_copy["court_name"] = court.court_name if court else "Unknown Court"
                booking_copy["booking_id"] = str(booking.id)
                user_bookings.append(booking_copy)
            return user_bookings

    @staticmethod
    async def get_all_bookings() -> List[Dict[str, Any]]:
        async with AsyncSessionLocal() as session:
            stmt = select(Booking)
            res = await session.execute(stmt)
            bookings = res.scalars().all()
            
            all_bookings = []
            for booking in bookings:
                court_stmt = select(Court).where(Court.id == booking.court_id)
                court_res = await session.execute(court_stmt)
                court = court_res.scalars().first()
                
                booking_copy = to_dict(booking)
                booking_copy["court_name"] = court.court_name if court else "Unknown Court"
                booking_copy["booking_id"] = str(booking.id)
                all_bookings.append(booking_copy)
            return all_bookings

    @staticmethod
    async def get_booking_by_id(booking_id: str) -> Optional[Dict[str, Any]]:
        if not booking_id:
            return None
        async with AsyncSessionLocal() as session:
            stmt = select(Booking).where(Booking.id == str(booking_id))
            res = await session.execute(stmt)
            booking = res.scalars().first()
            return to_dict(booking)

    @staticmethod
    async def is_slot_booked(court_id: str, booking_date: str, time_slot: str) -> bool:
        if not court_id:
            return False
        async with AsyncSessionLocal() as session:
            stmt = select(Booking).where(
                and_(
                    Booking.court_id == str(court_id),
                    Booking.booking_date == booking_date,
                    Booking.time_slot == time_slot,
                    Booking.status != "cancelled",
                    Booking.status != "payment_rejected"
                )
            )
            res = await session.execute(stmt)
            booking = res.scalars().first()
            return booking is not None

    @staticmethod
    async def has_user_booked_slot(user_id: str, booking_date: str, time_slot: str) -> bool:
        if not user_id:
            return False
        async with AsyncSessionLocal() as session:
            stmt = select(Booking).where(
                and_(
                    Booking.user_id == str(user_id),
                    Booking.booking_date == booking_date,
                    Booking.time_slot == time_slot,
                    Booking.status != "cancelled",
                    Booking.status != "payment_rejected"
                )
            )
            res = await session.execute(stmt)
            booking = res.scalars().first()
            return booking is not None

    @staticmethod
    async def create_booking(user_id: str, court_id: str, booking_date: str, time_slot: str) -> Dict[str, Any]:
        if not user_id or not court_id:
            raise ValueError("ID ไม่ถูกต้อง")
            
        async with AsyncSessionLocal() as session:
            new_booking = Booking(
                id=str(uuid.uuid4()),
                user_id=str(user_id),
                court_id=str(court_id),
                booking_date=booking_date,
                time_slot=time_slot,
                status="pending_payment",
                payment_id=None,
                created_at=datetime.now(timezone.utc)
            )
            session.add(new_booking)
            await session.commit()
            return to_dict(new_booking)

    @staticmethod
    async def cancel_booking(booking_id: str) -> Optional[Dict[str, Any]]:
        if not booking_id:
            return None
        async with AsyncSessionLocal() as session:
            stmt = select(Booking).where(Booking.id == str(booking_id))
            res = await session.execute(stmt)
            booking = res.scalars().first()
            if not booking:
                return None
            booking.status = "cancelled"
            await session.commit()
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
        async with AsyncSessionLocal() as session:
            # Query users where profile NTRP is between min and max AND phone must be verified
            stmt = select(User).where(
                and_(
                    User.role == "player",
                    User.profile['is_phone_verified'].as_boolean() == True,
                    User.profile['ntrp_rating'].as_float() >= ntrp_min,
                    User.profile['ntrp_rating'].as_float() <= ntrp_max
                )
            )
            res = await session.execute(stmt)
            users = res.scalars().all()
            
            compatible_matches = []
            for user in users:
                user_style = user.profile.get("playing_style")
                if preferred_playing_style and user_style != preferred_playing_style:
                    continue
                    
                # ดึงข้อมูลโปรไฟล์ทั้งหมดเพื่อส่งกลับ
                profile_data = user.profile or {}
                compatible_matches.append({
                    "user_id": str(user.id),
                    "username": user.username,
                    "ntrp": profile_data.get("ntrp_rating", 1.5),
                    "playing_style": profile_data.get("playing_style", "All-Court"),
                    "gender": profile_data.get("gender"),
                    "display_name": profile_data.get("display_name", user.username)
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
        if not host_user_id or not court_id:
            raise ValueError("ID ไม่ถูกต้อง")
            
        async with AsyncSessionLocal() as session:
            new_match = Match(
                id=str(uuid.uuid4()),
                host_user_id=str(host_user_id),
                invited_user_ids=[],
                court_id=str(court_id),
                match_date=match_date,
                time_slot=time_slot,
                match_type=match_type,
                ntrp_min=ntrp_min,
                ntrp_max=ntrp_max,
                status="open",
                created_at=datetime.now(timezone.utc)
            )
            session.add(new_match)
            await session.commit()
            return to_dict(new_match)

    @staticmethod
    async def get_match_by_id(match_id: str) -> Optional[Dict[str, Any]]:
        if not match_id:
            return None
        async with AsyncSessionLocal() as session:
            stmt = select(Match).where(Match.id == str(match_id))
            res = await session.execute(stmt)
            match_val = res.scalars().first()
            return to_dict(match_val)

    @staticmethod
    async def create_review(
        reviewer_id: str,
        match_id: str,
        reviewee_id: str,
        rating: int,
        comment: str
    ) -> Dict[str, Any]:
        if not reviewer_id or not match_id or not reviewee_id:
            raise ValueError("ID ไม่ถูกต้อง")
            
        async with AsyncSessionLocal() as session:
            new_review = Review(
                id=str(uuid.uuid4()),
                reviewer_id=str(reviewer_id),
                reviewee_id=str(reviewee_id),
                match_id=str(match_id),
                rating=rating,
                comment=comment,
                created_at=datetime.now(timezone.utc)
            )
            session.add(new_review)
            await session.commit()
            
            # 📊 คำนวณค่าดาวสะสมเฉลี่ย (Average rating) และจำนวนครั้งที่ถูกรีวิว (rating_count)
            avg_stmt = select(
                func.avg(Review.rating).label("avg_rating"),
                func.count(Review.id).label("cnt_rating")
            ).where(Review.reviewee_id == str(reviewee_id))
            
            avg_res = await session.execute(avg_stmt)
            avg_row = avg_res.first()
            
            avg_val = round(float(avg_row.avg_rating), 2) if avg_row and avg_row.avg_rating is not None else 5.0
            cnt_val = int(avg_row.cnt_rating) if avg_row and avg_row.cnt_rating is not None else 0
            
            # อัปเดตข้อมูลย้อนกลับเข้าไปใน Profile ของผู้ถูกรีวิว (Reviewee)
            user_stmt = select(User).where(User.id == str(reviewee_id))
            user_res = await session.execute(user_stmt)
            user = user_res.scalars().first()
            if user:
                updated_profile = dict(user.profile or {})
                updated_profile["rating_average"] = avg_val
                updated_profile["rating_count"] = cnt_val
                user.profile = updated_profile
                await session.commit()
                
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
        if not user_id or not booking_id:
            raise ValueError("ID ไม่ถูกต้อง")
            
        async with AsyncSessionLocal() as session:
            new_tx = Transaction(
                id=str(uuid.uuid4()),
                user_id=str(user_id),
                booking_id=str(booking_id),
                amount=amount,
                payment_method=payment_method,
                slip_url=slip_url,
                status="processing",
                created_at=datetime.now(timezone.utc),
                verified_at=None
            )
            session.add(new_tx)
            
            # อัปเดตสถานะของ Booking ด้วย
            booking_stmt = select(Booking).where(Booking.id == str(booking_id))
            booking_res = await session.execute(booking_stmt)
            booking = booking_res.scalars().first()
            if booking:
                booking.payment_id = new_tx.id
                booking.status = "pending_verification"
                
            await session.commit()
            return to_dict(new_tx)

    @staticmethod
    async def get_pending_transactions() -> List[Dict[str, Any]]:
        async with AsyncSessionLocal() as session:
            stmt = select(Transaction).where(Transaction.status == "processing")
            res = await session.execute(stmt)
            transactions = res.scalars().all()
            
            pending = []
            for tx in transactions:
                booking_stmt = select(Booking).where(Booking.id == tx.booking_id)
                booking_res = await session.execute(booking_stmt)
                booking = booking_res.scalars().first()
                
                court = None
                if booking:
                    court_stmt = select(Court).where(Court.id == booking.court_id)
                    court_res = await session.execute(court_stmt)
                    court = court_res.scalars().first()
                    
                user_stmt = select(User).where(User.id == tx.user_id)
                user_res = await session.execute(user_stmt)
                user = user_res.scalars().first()
                
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
        if not tx_id:
            return None
        async with AsyncSessionLocal() as session:
            stmt = select(Transaction).where(Transaction.id == str(tx_id))
            res = await session.execute(stmt)
            tx = res.scalars().first()
            return to_dict(tx)

    @staticmethod
    async def verify_payment(tx_id: str, action: str) -> Optional[Dict[str, Any]]:
        if not tx_id:
            return None
        async with AsyncSessionLocal() as session:
            stmt = select(Transaction).where(Transaction.id == str(tx_id))
            res = await session.execute(stmt)
            tx = res.scalars().first()
            if not tx:
                return None
                
            booking_stmt = select(Booking).where(Booking.id == tx.booking_id)
            booking_res = await session.execute(booking_stmt)
            booking = booking_res.scalars().first()
            
            if action == "approve":
                tx.status = "verified"
                tx.verified_at = datetime.now(timezone.utc)
                if booking:
                    booking.status = "confirmed"
            elif action == "reject":
                tx.status = "failed"
                if booking:
                    booking.status = "payment_rejected"
                    
            await session.commit()
            return to_dict(tx)

    # 📊 7. Dashboard Stats
    @staticmethod
    async def get_dashboard_stats() -> Dict[str, Any]:
        async with AsyncSessionLocal() as session:
            user_count_res = await session.execute(select(func.count()).select_from(User))
            user_count = user_count_res.scalar()
            
            court_count_res = await session.execute(select(func.count()).select_from(Court))
            court_count = court_count_res.scalar()
            
            match_count_res = await session.execute(select(func.count()).select_from(Match).where(Match.status == "open"))
            match_count = match_count_res.scalar()
            
            return {
                "total_active_users": user_count,
                "available_courts_today": court_count,
                "upcoming_matches_count": match_count,
                "system_announcement": "ยินดีต้อนรับสู่สนาม Impact Tennis! มีโปรโมชั่นช่วงบ่ายลด 20%"
            }

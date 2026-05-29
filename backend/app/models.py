from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field
# pyrefly: ignore [missing-import]
from beanie import Document, PydanticObjectId
# pyrefly: ignore [missing-import]
from pymongo import IndexModel, ASCENDING

# ----------------- Sub-Models -----------------

class UserProfile(BaseModel):
    model_config = {"extra": "allow"}  # อนุญาตฟิลด์เพิ่มเติมจากข้อมูล seed

    display_name: str
    phone: str
    is_phone_verified: bool = False
    ntrp_rating: float = 1.5 # ระดับฝีมือ 1.5 - 7.0
    wtn_rating: float = 40.0 # ระดับฝีมือ 40 - 1
    playing_style: str = "All-Court" # "Aggressive Baseliner", "Serve & Volley", etc.
    match_preference: str = "any" # "equal", "higher", "lower", "any"
    gender: Optional[str] = None # "male", "female", "other"
    birthday: Optional[str] = None # รูปแบบ YYYY-MM-DD
    nationality: Optional[str] = None # "thai", "american", etc.
    vip: bool = False # สถานะ VIP
    points: int = 0 # คะแนนสะสม

class AvailableSlot(BaseModel):
    time_slot: str
    is_booked: bool = False

# ----------------- Beanie Documents (Collections) -----------------

class User(Document):
    username: str
    email: str
    password_hash: Optional[str] = None # เก็บ Hash รหัสผ่าน (เว้นว่างได้ถ้าใช้ Google OAuth)
    google_id: Optional[str] = None # สำหรับล็อกอินด้วย Google SSO
    role: str = "player" # "player", "admin", "court_owner"
    profile: UserProfile
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "users" # ชื่อคอลเลกชันใน MongoDB
        indexes = [
            IndexModel([("email", ASCENDING)], unique=True),
        ]

class Court(Document):
    court_name: str
    location: str
    price_per_hour: float
    available_slots: List[AvailableSlot] = []

    class Settings:
        name = "courts"

class Booking(Document):
    user_id: PydanticObjectId # อ้างอิงไปยัง User
    court_id: PydanticObjectId # อ้างอิงไปยัง Court
    booking_date: str # รูปแบบ YYYY-MM-DD
    time_slot: str # เช่น "18:00-20:00"
    status: str = "pending" # "pending", "confirmed", "cancelled"
    payment_id: Optional[PydanticObjectId] = None # อ้างอิงไปยัง Transaction
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "bookings"
        indexes = [
            IndexModel([("court_id", ASCENDING), ("booking_date", ASCENDING), ("time_slot", ASCENDING)]),
            IndexModel([("user_id", ASCENDING)]),
        ]

class Match(Document):
    host_user_id: PydanticObjectId # ผู้สร้างแมตช์
    invited_user_ids: List[PydanticObjectId] = [] # ผู้เล่นที่เข้ามาร่วม
    court_id: PydanticObjectId
    match_date: str # รูปแบบ YYYY-MM-DD
    time_slot: str # เช่น "18:00-20:00"
    match_type: str = "singles" # "singles" / "doubles"
    ntrp_min: float = 1.5
    ntrp_max: float = 7.0
    status: str = "open" # "open", "matched", "cancelled"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "matches"

class Review(Document):
    reviewer_id: PydanticObjectId # คนส่งคะแนน
    reviewee_id: PydanticObjectId # คนที่ได้รับการประเมิน
    match_id: PydanticObjectId # ไอดีแมตช์ที่เกี่ยวเนื่อง
    rating: int = Field(default=5, ge=1, le=5) # 1 - 5 ดาว
    comment: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "reviews"

class Transaction(Document):
    user_id: PydanticObjectId
    booking_id: PydanticObjectId # อ้างอิงไปยัง Booking
    amount: float
    payment_method: str # "PromptPay", "BankTransfer"
    slip_url: str # ที่อยู่ภาพสลิปที่เก็บไว้
    status: str = "pending" # "pending", "verified", "failed"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    verified_at: Optional[datetime] = None

    class Settings:
        name = "transactions"
        indexes = [
            IndexModel([("status", ASCENDING)]),
        ]

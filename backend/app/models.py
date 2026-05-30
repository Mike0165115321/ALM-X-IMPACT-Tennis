import uuid
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field
# pyrefly: ignore [missing-import]
from sqlalchemy import Column, String, Float, Integer, DateTime, JSON, UniqueConstraint, Boolean
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# ----------------- Pydantic Sub-Models (For validation and UI Contract) -----------------

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
    points: int = 0 # คะแนนคงเหลือปัจจุบันสำหรับการแลก (เดิม)
    member_tier: str = "Standard" # "Standard", "Silver", "Gold", "Platinum"
    accumulated_points: int = 0 # คะแนนสะสมทั้งหมดสำหรับอัปเกรดระดับสมาชิก
    current_points: int = 0 # คะแนนสะสมคงเหลือปัจจุบัน


class AvailableSlot(BaseModel):
    time_slot: str
    is_booked: bool = False

# ----------------- SQLAlchemy Declarative Models (Supabase Tables) -----------------

class User(Base):
    __tablename__ = "alm_users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=True)
    role = Column(String, default="player")
    profile = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Court(Base):
    __tablename__ = "alm_courts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    court_name = Column(String, nullable=False)
    location = Column(String, nullable=False)
    price_per_hour = Column(Float, nullable=False)
    available_slots = Column(JSON, nullable=False, default=list)

class Booking(Base):
    __tablename__ = "alm_bookings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    court_id = Column(String, nullable=False, index=True)
    booking_date = Column(String, nullable=False, index=True)
    time_slot = Column(String, nullable=False, index=True)
    status = Column(String, default="pending")
    payment_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Match(Base):
    __tablename__ = "alm_matches"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    host_user_id = Column(String, nullable=False, index=True)
    invited_user_ids = Column(JSON, nullable=False, default=list)
    court_id = Column(String, nullable=False)
    match_date = Column(String, nullable=False)
    time_slot = Column(String, nullable=False)
    match_type = Column(String, default="singles")
    ntrp_min = Column(Float, default=1.5)
    ntrp_max = Column(Float, default=7.0)
    status = Column(String, default="open")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Review(Base):
    __tablename__ = "alm_reviews"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    reviewer_id = Column(String, nullable=False)
    reviewee_id = Column(String, nullable=False)
    match_id = Column(String, nullable=False)
    rating = Column(Integer, default=5)
    comment = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Transaction(Base):
    __tablename__ = "alm_transactions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    booking_id = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    payment_method = Column(String, nullable=False)
    slip_url = Column(String, nullable=False)
    status = Column(String, default="pending", index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    verified_at = Column(DateTime(timezone=True), nullable=True)

class Coach(Base):
    __tablename__ = "alm_coaches"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    price_per_hour = Column(Float, nullable=False)
    specialties = Column(JSON, nullable=False, default=list)
    rating = Column(Float, default=5.0)
    experience_years = Column(Integer, default=0)
    available_slots = Column(JSON, nullable=False, default=list)

class CoachBooking(Base):
    __tablename__ = "alm_coach_bookings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    coach_id = Column(String, nullable=False, index=True)
    booking_date = Column(String, nullable=False, index=True)
    time_slot = Column(String, nullable=False, index=True)
    status = Column(String, default="pending_payment")
    payment_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Merchandise(Base):
    __tablename__ = "alm_merchandise"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    item_name = Column(String, nullable=False)
    category = Column(String, nullable=False) # drink, ball, racket_rental
    price = Column(Float, nullable=False)
    stock_quantity = Column(Integer, default=100)
    is_rental = Column(Boolean, default=False)

class Order(Base):
    __tablename__ = "alm_orders"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    court_booking_id = Column(String, nullable=True)
    items = Column(JSON, nullable=False, default=list)
    total_price = Column(Float, nullable=False)
    status = Column(String, default="pending_payment")
    payment_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

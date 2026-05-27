import uuid
from datetime import datetime
from typing import Dict, List, Any

# ข้อมูลจำลองสำหรับระบบ In-Memory Database

# ตัวช่วยสร้าง ID เลียนแบบ MongoDB ObjectId
def generate_id() -> str:
    return uuid.uuid4().hex[:24]

# คีย์ไอดีหลักสำหรับการจับคู่ข้อมูล
USER_1_ID = "60d5ec4b2f8fb8123456789a"  # tennis_player_1
USER_2_ID = "60d5ec4b2f8fb8123456789b"  # net_rusher
USER_ADMIN_ID = "60d5ec4b2f8fb8123456789c"  # admin_user

COURT_1_ID = "60d5ec4b2f8fb8123456789d"  # Impact Court A
COURT_2_ID = "60d5ec4b2f8fb8123456789e"  # Impact Court B

MATCH_1_ID = "60d5ec4b2f8fb8123456789f"

mock_users: Dict[str, Dict[str, Any]] = {
    USER_1_ID: {
        "id": USER_1_ID,
        "username": "tennis_lover",
        "email": "user1@example.com",
        "password_hash": "$2b$12$EixZaYVK1fsAH1iyxS/ehuM2zL2y10d8v.2gP37o11PZ/P5j1s/0q",  # bcrypt hash ของ "securepassword123"
        "google_id": None,
        "role": "player",
        "profile": {
            "display_name": "Somchai Tennis",
            "phone": "0812345678",
            "is_phone_verified": True,
            "ntrp_rating": 3.0,
            "wtn_rating": 25.0,
            "playing_style": "Aggressive Baseliner",
            "match_preference": "any"
        },
        "created_at": datetime.utcnow()
    },
    USER_2_ID: {
        "id": USER_2_ID,
        "username": "net_rusher",
        "email": "user2@example.com",
        "password_hash": "$2b$12$EixZaYVK1fsAH1iyxS/ehuM2zL2y10d8v.2gP37o11PZ/P5j1s/0q",
        "google_id": None,
        "role": "player",
        "profile": {
            "display_name": "Somsak NetPlay",
            "phone": "0898765432",
            "is_phone_verified": True,
            "ntrp_rating": 3.5,
            "wtn_rating": 20.0,
            "playing_style": "Serve & Volley",
            "match_preference": "equal"
        },
        "created_at": datetime.utcnow()
    },
    USER_ADMIN_ID: {
        "id": USER_ADMIN_ID,
        "username": "admin_impact",
        "email": "admin@impacttennis.com",
        "password_hash": "$2b$12$hH20AoWb6Ii7t/da8AWlMenEYMKQYLoXd/fR6lP7IRbXt0TgfmVDq",
        "google_id": None,
        "role": "admin",
        "profile": {
            "display_name": "Admin Impact",
            "phone": "021234567",
            "is_phone_verified": True,
            "ntrp_rating": 4.0,
            "wtn_rating": 15.0,
            "playing_style": "All-Court",
            "match_preference": "any"
        },
        "created_at": datetime.utcnow()
    }
}

mock_courts: Dict[str, Dict[str, Any]] = {
    COURT_1_ID: {
        "id": COURT_1_ID,
        "court_name": "Impact Court A (Indoor)",
        "location": "Impact Tennis Club - Zone A",
        "price_per_hour": 500.0,
        "available_slots": [
            {"time_slot": "16:00-17:00", "is_booked": False},
            {"time_slot": "17:00-18:00", "is_booked": False},
            {"time_slot": "18:00-19:00", "is_booked": True},
            {"time_slot": "19:00-20:00", "is_booked": True},
            {"time_slot": "20:00-21:00", "is_booked": False}
        ]
    },
    COURT_2_ID: {
        "id": COURT_2_ID,
        "court_name": "Impact Court B (Outdoor)",
        "location": "Impact Tennis Club - Zone B",
        "price_per_hour": 350.0,
        "available_slots": [
            {"time_slot": "16:00-17:00", "is_booked": False},
            {"time_slot": "17:00-18:00", "is_booked": False},
            {"time_slot": "18:00-19:00", "is_booked": False},
            {"time_slot": "19:00-20:00", "is_booked": False},
            {"time_slot": "20:00-21:00", "is_booked": False}
        ]
    }
}

mock_bookings: Dict[str, Dict[str, Any]] = {
    "booking_1": {
        "id": "booking_1",
        "user_id": USER_1_ID,
        "court_id": COURT_1_ID,
        "booking_date": "2026-05-25",
        "time_slot": "18:00-20:00",
        "status": "confirmed",
        "payment_id": "tx_1",
        "created_at": datetime.utcnow()
    },
    "booking_2": {
        "id": "booking_2",
        "user_id": USER_2_ID,
        "court_id": COURT_2_ID,
        "booking_date": "2026-05-28",
        "time_slot": "16:00-17:00",
        "status": "pending_verification",
        "payment_id": "tx_pending_test",
        "created_at": datetime.utcnow()
    }
}

mock_matches: Dict[str, Dict[str, Any]] = {
    MATCH_1_ID: {
        "id": MATCH_1_ID,
        "host_user_id": USER_1_ID,
        "invited_user_ids": [USER_2_ID],
        "court_id": COURT_1_ID,
        "match_date": "2026-05-25",
        "time_slot": "18:00-20:00",
        "match_type": "singles",
        "ntrp_min": 2.5,
        "ntrp_max": 4.0,
        "status": "matched",
        "created_at": datetime.utcnow()
    }
}

mock_reviews: Dict[str, Dict[str, Any]] = {
    "review_1": {
        "id": "review_1",
        "reviewer_id": USER_1_ID,
        "reviewee_id": USER_2_ID,
        "match_id": MATCH_1_ID,
        "rating": 5,
        "comment": "เล่นสนุกมาก คุมหน้าเน็ตได้ดี สุภาพมาก",
        "created_at": datetime.utcnow()
    }
}

mock_transactions: Dict[str, Dict[str, Any]] = {
    "tx_1": {
        "id": "tx_1",
        "user_id": USER_1_ID,
        "booking_id": "booking_1",
        "amount": 1000.0,
        "payment_method": "PromptPay",
        "slip_url": "https://storage.googleapis.com/alm-tennis-slips/slip_1.jpg",
        "status": "verified",
        "verified_at": datetime.utcnow()
    },
    "tx_pending_test": {
        "id": "tx_pending_test",
        "user_id": USER_2_ID,
        "booking_id": "booking_2",
        "amount": 350.0,
        "payment_method": "BankTransfer",
        "slip_url": "https://storage.googleapis.com/alm-tennis-slips/slip_pending.jpg",
        "status": "processing",
        "created_at": datetime.utcnow(),
        "verified_at": None
    }
}

# OTP Temporary Store (phone -> {otp_code, ref_code, expires_at})
mock_otp_store: Dict[str, Dict[str, Any]] = {}

# 📂 โหลดข้อมูลผู้ใช้เพิ่มเติมจากไฟล์ seeded_users.json (หากมีอยู่จากการอิมพอร์ต CSV)
import os
import json
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    seeded_file_path = os.path.join(current_dir, "seeded_users.json")
    if os.path.exists(seeded_file_path):
        with open(seeded_file_path, "r", encoding="utf-8") as f:
            seeded_data = json.load(f)
            # ผสานข้อมูลประชากรผู้ใช้ 767 คนเข้าร่วมใน In-Memory DB
            mock_users.update(seeded_data)
except Exception as e:
    import logging
    logging.getLogger("backend").warning(f"ไม่สามารถโหลดไฟล์ seeded_users.json ได้: {str(e)}")


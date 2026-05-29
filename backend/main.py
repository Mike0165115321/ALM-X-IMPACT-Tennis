import logging
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
# pyrefly: ignore [missing-import]
from motor.motor_asyncio import AsyncIOMotorClient
# pyrefly: ignore [missing-import]
from beanie import init_beanie

from app.config import settings
from app.services.data_service import DataService
from app.logger import setup_logging
from app.exceptions import ALMException
from app.services.storage_service import StorageService

# เริ่มตั้งค่าระบบ Logging คลุมทั้งแอปพลิเคชัน (Console และ File)
setup_logging()

# เลือกระดับ logger ของระบบหลังบ้าน
logger = logging.getLogger("backend")

# นำเข้า Routers ทั้งหมด
from app.routers import auth, queues, matching, reviews, payments, courts, admin

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 🔌 [MongoDB Mode] กำลังเชื่อมต่อฐานข้อมูล MongoDB...
    app.state.db_ready = False
    logger.info("🔌 กำลังเชื่อมต่อฐานข้อมูล MongoDB...")
    try:
        from app.models import User, Court, Booking, Match, Review, Transaction
        
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        await init_beanie(
            database=client[settings.DATABASE_NAME],
            document_models=[User, Court, Booking, Match, Review, Transaction]
        )
        logger.info("✅ เชื่อมต่อ MongoDB และ Beanie Models สำเร็จ!")
        app.state.db_ready = True
        
        # 📂 ระบบ Seeding อัตโนมัติในครั้งแรกที่เปิดเซิร์ฟเวอร์
        user_count = await User.count()
        if user_count == 0:
            logger.info("🌱 [Database Seed] กำลังนำเข้าข้อมูลประชากรผู้ใช้ 767 คนเข้าสู่ MongoDB...")
            import json
            import os
            
            # ตรวจสอบไฟล์ seeded_users.json
            current_dir = os.path.dirname(os.path.abspath(__file__))
            seeded_file_path = os.path.join(current_dir, "app", "services", "seeded_users.json")
            if os.path.exists(seeded_file_path):
                with open(seeded_file_path, "r", encoding="utf-8") as f:
                    seeded_data = json.load(f)
                    
                users_to_insert = []
                inserted_emails = set()
                skipped = 0
                for u_id, u_data in seeded_data.items():
                    try:
                        # แปลง created_at String กลับเป็น datetime
                        try:
                            c_at = datetime.fromisoformat(u_data["created_at"])
                        except Exception:
                            c_at = datetime.now(timezone.utc)
                        
                        # สร้าง User โดยไม่กำหนด id (ให้ MongoDB สร้าง ObjectId เอง)
                        profile_data = u_data.get("profile", {})
                        email_val = u_data.get("email")
                        if not email_val:
                            email_val = f"no_email_{u_id}@alm-impact-tennis.com"
                        
                        email_lower = email_val.lower().strip()
                        if email_lower in inserted_emails:
                            # หากพบอีเมลซ้ำ ให้แปลงให้ไม่ซ้ำเพื่อรองรับ unique index ใน MongoDB
                            email_lower = f"dup_{u_id[:8]}_{email_lower}"
                        
                        inserted_emails.add(email_lower)
                        
                        pwd_hash = u_data.get("password_hash")
                        user_role = u_data.get("role", "player")
                        if user_role == "admin":
                            from app.utils import hash_password
                            pwd_hash = hash_password("securepassword123")
                        
                        user_doc = User(
                            username=u_data["username"],
                            email=email_lower,
                            password_hash=pwd_hash,
                            google_id=u_data.get("google_id"),
                            role=user_role,
                            profile=profile_data,
                            created_at=c_at
                        )
                        users_to_insert.append(user_doc)
                    except Exception as user_err:
                        skipped += 1
                        logger.warning(f"⚠️ [Seed Skip] ข้ามผู้ใช้ {u_data.get('username', u_id)}: {str(user_err)}")
                
                if users_to_insert:
                    await User.insert_many(users_to_insert)
                    logger.info(f"🌱 [Database Seed] นำเข้าผู้ใช้ {len(users_to_insert)} คนสำเร็จ! (ข้าม {skipped} คน)")
            
            # นำเข้าข้อมูลสนามเทนนิสเริ่มต้น 2 คอร์ท
            court_count = await Court.count()
            if court_count == 0:
                logger.info("🌱 [Database Seed] สร้างสนามเทนนิสเริ่มต้น 2 คอร์ท...")
                court_a = Court(
                    court_name="Impact Court A (Indoor)",
                    location="Impact Tennis Club - Zone A",
                    price_per_hour=500.0,
                    available_slots=[
                        {"time_slot": "16:00-17:00", "is_booked": False},
                        {"time_slot": "17:00-18:00", "is_booked": False},
                        {"time_slot": "18:00-19:00", "is_booked": False},
                        {"time_slot": "19:00-20:00", "is_booked": False},
                        {"time_slot": "20:00-21:00", "is_booked": False}
                    ]
                )
                court_b = Court(
                    court_name="Impact Court B (Outdoor)",
                    location="Impact Tennis Club - Zone B",
                    price_per_hour=350.0,
                    available_slots=[
                        {"time_slot": "16:00-17:00", "is_booked": False},
                        {"time_slot": "17:00-18:00", "is_booked": False},
                        {"time_slot": "18:00-19:00", "is_booked": False},
                        {"time_slot": "19:00-20:00", "is_booked": False},
                        {"time_slot": "20:00-21:00", "is_booked": False}
                    ]
                )
                await Court.insert_many([court_a, court_b])
                logger.info("🌱 [Database Seed] สร้างสนามสำเร็จ!")
    except Exception as e:
        logger.error(f"❌ [Database Error] ไม่สามารถเชื่อมต่อหรือเริ่มระบบฐานข้อมูลได้: {str(e)}")
        
    yield

app = FastAPI(
    title="ALM-X-IMPACT Tennis API",
    description="ระบบหลังบ้านจองสนามเทนนิสและหาคู่เล่นระดับอัจฉริยะ (NTRP Matchmaking)",
    version="1.0.0",
    lifespan=lifespan
)

# 🌐 Config CORS (เปิดรับการร้องขอจาก Wix.com ทุกโดเมนเพื่อทดสอบและใช้งาน)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📂 เริ่มต้นระบบจัดเก็บไฟล์ผ่าน StorageService (เปลี่ยนพฤติกรรมฝั่งคลาวด์/จำลองในไฟล์โมดูลนั้นได้เลย)
StorageService.init_app(app)

# ลงทะเบียน Routers เข้ากับ App หลัก
app.include_router(auth.router)
app.include_router(queues.router)
app.include_router(matching.router)
app.include_router(reviews.router)
app.include_router(payments.router)
app.include_router(courts.router)
app.include_router(admin.router)

# 🛠️ Global Exception Handler สำหรับ ALMException
@app.exception_handler(ALMException)
async def alm_exception_handler(request: Request, exc: ALMException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.message
        }
    )

# 📍 API Endpoint หน้าโฮม
@app.get("/")
def read_root():
    return {
        "status": "success",
        "message": "ยินดีต้อนรับเข้าสู่ระบบหลังบ้าน ALM-X-IMPACT Tennis API",
        "docs_url": "/docs"
    }

# 📍 API Endpoint ตัวอย่างตามสัญญา API ข้อ 6
@app.get("/api/v1/data")
async def get_dashboard_data():
    return await DataService.get_dashboard_stats()

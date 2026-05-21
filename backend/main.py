import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from app.config import settings
from app.models import User, Court, Booking, Match, Review, Transaction

# ตั้งค่า Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend")

app = FastAPI(
    title="ALM-X-IMPACT Tennis API",
    description="ระบบหลังบ้านจองสนามเทนนิสและหาคู่เล่นระดับอัจฉริยะ (NTRP Matchmaking)",
    version="1.0.0"
)

# 🌐 Config CORS (เพื่อให้ Next.js Port 3000 เรียกใช้ FastAPI ได้)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🚀 ทำงานตอนระบบกำลังเปิดตัว (Database Initialization)
@app.on_event("startup")
async def startup_event():
    logger.info("กำลังเชื่อมต่อฐานข้อมูล MongoDB...")
    try:
        # เปิดการเชื่อมต่อ Async กับ MongoDB
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        
        # เริ่มต้นใช้งาน Beanie พร้อมผูกคอลเลกชันเอกสาร
        await init_beanie(
            database=client[settings.DATABASE_NAME],
            document_models=[
                User,
                Court,
                Booking,
                Match,
                Review,
                Transaction
            ]
        )
        logger.info("เชื่อมต่อ MongoDB และเริ่มต้นระบบ Beanie ODM สำเร็จ!")
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการเปิดระบบฐานข้อมูล: {e}")

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
    # ข้อมูลจำลองตาม API Contract
    return {
        "total_active_users": 152,
        "available_courts_today": 8,
        "upcoming_matches_count": 14,
        "system_announcement": "ยินดีต้อนรับสู่สนาม Impact Tennis! มีโปรโมชั่นช่วงบ่ายลด 20%"
    }

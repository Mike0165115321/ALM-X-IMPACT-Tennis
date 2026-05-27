import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# pyrefly: ignore [missing-import]
from motor.motor_asyncio import AsyncIOMotorClient
# pyrefly: ignore [missing-import]
from beanie import init_beanie

from app.config import settings
from app.services.data_service import DataService

# นำเข้า Routers ทั้งหมดที่สร้างขึ้นใหม่
from app.routers import auth, queues, matching, reviews, payments

# ตั้งค่า Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend")

app = FastAPI(
    title="ALM-X-IMPACT Tennis API",
    description="ระบบหลังบ้านจองสนามเทนนิสและหาคู่เล่นระดับอัจฉริยะ (NTRP Matchmaking)",
    version="1.0.0"
)

# 🌐 Config CORS (เปิดรับการร้องขอจาก Wix.com ทุกโดเมนเพื่อทดสอบและใช้งาน)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ลงทะเบียน Routers เข้ากับ App หลัก
app.include_router(auth.router)
app.include_router(queues.router)
app.include_router(matching.router)
app.include_router(reviews.router)
app.include_router(payments.router)

# 🚀 ทำงานตอนระบบกำลังเปิดตัว (ข้ามการเชื่อมต่อฐานข้อมูลสำหรับการทดสอบ API หน้าบ้าน)
@app.on_event("startup")
async def startup_event():
    logger.info("⚠️ [API Test Mode] ข้ามการเชื่อมต่อฐานข้อมูล MongoDB ชั่วคราว...")

# 📍 API Endpoint หน้าโฮม
@app.get("/")
def read_root():
    return {
        "status": "success",
        "message": "ยินดีต้อนรับเข้าสู่ระบบหลังบ้าน ALM-X-IMPACT Tennis API",
        "docs_url": "/docs"
    }

# 📍 API Endpoint ตัวอย่างตามสัญญา API ข้อ 6 (ปรับให้ดึงจาก DataService จำลอง)
@app.get("/api/v1/data")
async def get_dashboard_data():
    return DataService.get_dashboard_stats()


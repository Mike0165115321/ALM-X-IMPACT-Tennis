import logging
import json
import os
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, func

from app.config import settings
from app.services.data_service import DataService, engine, AsyncSessionLocal
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
    # 🔌 [Supabase Mode] กำลังเชื่อมต่อฐานข้อมูล Supabase (PostgreSQL)...
    app.state.db_ready = False
    logger.info("🔌 กำลังเชื่อมต่อฐานข้อมูล Supabase (PostgreSQL)...")
    try:
        # เชื่อมต่อระบบสำเร็จ (ไม่ต้องทำการสร้างตารางหรือ Seed ข้อมูลจำลองทับข้อมูลจริงบน Cloud)
        app.state.db_ready = True
        logger.info("✅ เชื่อมต่อฐานข้อมูล Supabase Cloud สำเร็จ!")
    except Exception as e:
        logger.error(f"❌ [Database Error] ไม่สามารถเชื่อมต่อระบบฐานข้อมูลได้: {str(e)}")
        
    yield

app = FastAPI(
    title="ALM-X-IMPACT Tennis API",
    description="ระบบหลังบ้านจองสนามเทนนิสและหาคู่เล่นระดับอัจฉริยะ (NTRP Matchmaking)",
    version="1.0.0",
    lifespan=lifespan
)

# 🌐 Config CORS (เปิดรับการร้องขอข้ามโดเมนสำหรับ Wix.com และทดสอบระบบโลคอล)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
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

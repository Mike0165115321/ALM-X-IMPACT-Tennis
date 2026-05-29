import random
import string
import logging
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any

from app.services.data_service import DataService
from app.utils import create_access_token, verify_password, decode_access_token, hash_password

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])
security = HTTPBearer()
logger = logging.getLogger("auth")

# ----------------- Pydantic Request/Response Models -----------------

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str = Field(..., min_length=8, description="รหัสผ่านต้องมีความยาวอย่างน้อย 8 ตัวอักษร")
    phone: str = Field(..., pattern=r"^0\d{9}$", description="เบอร์โทรศัพท์มือถือไทย 10 หลัก (เช่น 0812345678)")

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class GoogleLoginRequest(BaseModel):
    id_token: str

class OTPSendRequest(BaseModel):
    phone: str

class OTPVerifyRequest(BaseModel):
    phone: str
    otp_code: str
    ref_code: str

# ----------------- Auth Helpers & Dependencies -----------------

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="โทเค็นหมดอายุหรือไม่ถูกต้อง",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ข้อมูลโทเค็นไม่สมบูรณ์",
        )
    user = await DataService.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ไม่พบผู้ใช้ในระบบ",
        )
    return user

# ----------------- Route Endpoints -----------------

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest):
    # ตรวจสอบอีเมลซ้ำ
    existing_user = await DataService.get_user_by_email(payload.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="อีเมลนี้ถูกใช้งานแล้วในระบบ"
        )
    
    # แฮชรหัสผ่าน
    pwd_hash = hash_password(payload.password)
    
    # สร้างผู้ใช้ใหม่
    user = await DataService.create_user(
        username=payload.username,
        email=payload.email,
        password_hash=pwd_hash,
        role="player",
        profile={
            "phone": payload.phone,
            "is_phone_verified": False
        }
    )
    
    # สร้าง JWT Token
    access_token = create_access_token(data={"sub": user["id"], "role": user["role"]})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"],
            "is_phone_verified": user["profile"]["is_phone_verified"]
        }
    }

@router.post("/login")
async def login(payload: LoginRequest):
    user = await DataService.get_user_by_email(payload.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="อีเมลหรือรหัสผ่านไม่ถูกต้อง"
        )
    
    if not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="อีเมลหรือรหัสผ่านไม่ถูกต้อง"
        )
        
    access_token = create_access_token(data={"sub": user["id"], "role": user["role"]})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"],
            "is_phone_verified": user["profile"]["is_phone_verified"]
        }
    }

@router.post("/google")
async def google_login(payload: GoogleLoginRequest):
    # ในการทดสอบ Mock เราจะจำลองการถอดรหัส Google Token
    # หากเป็นโทเค็นจำลอง เราจะสร้าง/ดึงข้อมูลจำลอง
    email = "google_user@gmail.com"
    username = "tennis_player_sso"
    google_id = "google_sso_123456789"
    
    user = await DataService.get_user_by_google_id(google_id)
    if not user:
        user = await DataService.create_user(
            username=username,
            email=email,
            google_id=google_id,
            role="player",
            profile={
                "display_name": "Google SSO Player",
                "phone": "0968013963",
                "is_phone_verified": False,
                "ntrp_rating": 2.5
            }
        )
        
    access_token = create_access_token(data={"sub": user["id"], "role": user["role"]})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"],
            "is_phone_verified": user["profile"]["is_phone_verified"]
        }
    }

@router.post("/otp/send")
async def send_otp(payload: OTPSendRequest):
    # ตรวจสอบ Rate Limit 3 ครั้งใน 15 นาที
    if not await DataService.check_otp_rate_limit(payload.phone):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="ร้องขอ OTP บ่อยเกินไป กรุณารองในอีก 15 นาที"
        )
        
    # สุ่มเลข OTP และ Ref Code
    otp_code = "".join(random.choices(string.digits, k=6))
    ref_code = "".join(random.choices(string.ascii_uppercase, k=4))
    
    await DataService.save_otp(payload.phone, otp_code, ref_code)
    
    # ดึง SMS Service มายิงจริง (ยกเว้นเบอร์ทดสอบระบบที่เริ่มต้นด้วย 087 ของ Pytest)
    from app.config import settings
    is_test_phone = settings.ENABLE_OTP_BYPASS and payload.phone.startswith("087")
    if is_test_phone:
        logger.debug(f"🔥 [SMS OTP SIMULATOR - PYTEST] Sent OTP: {otp_code} (Ref: {ref_code}) to {payload.phone}")
        success = True
    else:
        from app.services.sms_service import SMSService
        success = await SMSService.send_otp_sms(payload.phone, otp_code, ref_code)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="ไม่สามารถส่งข้อความ OTP ไปยังเบอร์โทรศัพท์นี้ได้ในขณะนี้"
        )
    
    return {
        "message": f"OTP sent successfully to {payload.phone}",
        "ref_code": ref_code
    }

@router.post("/otp/verify")
async def verify_otp(payload: OTPVerifyRequest):
    success = await DataService.verify_otp(payload.phone, payload.otp_code, payload.ref_code)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="รหัส OTP หรือ Ref Code ไม่ถูกต้อง หรืออาจจะหมดอายุ (จำกัดเวลา 5 นาที)"
        )
    return {
        "status": "success",
        "message": "Phone number verified successfully"
    }

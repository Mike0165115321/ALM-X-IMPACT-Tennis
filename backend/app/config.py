import os
from dotenv import load_dotenv

# โหลดค่าจากไฟล์ .env
load_dotenv()

class Settings:
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")

    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "alm_impact_tennis")

    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "super_secret_jwt_key_change_me_in_production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

    # CORS & OTP Bypass Settings
    CORS_ALLOWED_ORIGINS: list[str] = [
        origin.strip() for origin in os.getenv("CORS_ALLOWED_ORIGINS", "*").split(",") if origin.strip()
    ]
    ENABLE_OTP_BYPASS: bool = os.getenv("ENABLE_OTP_BYPASS", "true").lower() in ("true", "1", "yes")

    # SMS Settings
    SMS_API_KEY: str = os.getenv("SMS_API_KEY", "")
    SMS_API_SECRET: str = os.getenv("SMS_API_SECRET", "")
    SMS_SENDER_NAME: str = os.getenv("SMS_SENDER_NAME", "SMS")
    SMS_OTP_API_URL: str = os.getenv("SMS_OTP_API_URL", "https://otp.thaibulksms.com/v1/otp")

    # Google SSO Settings
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")

    def __init__(self):
        # 🐳 ดักจับอัตโนมัติหากรันแอปพลิเคชันอยู่ภายในตู้คอนเทนเนอร์ Docker (WSL/Compose Network)
        # ให้ทำการสลับ URL การเชื่อมต่อไปยังโฮสต์ 'mongodb' ที่เป็น Service Name แทน 'localhost' ทันที
        if os.path.exists("/.dockerenv") and self.MONGODB_URL == "mongodb://localhost:27017":
            self.MONGODB_URL = "mongodb://mongodb:27017"

settings = Settings()


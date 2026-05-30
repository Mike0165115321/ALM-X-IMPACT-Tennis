import os
from dotenv import load_dotenv

# โหลดค่าจากไฟล์ .env
load_dotenv()

class Settings:
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")

    SUPABASE_DB_URL: str = os.getenv("SUPABASE_DB_URL", os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"))

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

    # SMTP Settings (Hotmail/Outlook)
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp-mail.outlook.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_NAME: str = os.getenv("SMTP_FROM_NAME", "IMPACT Tennis Club")

    def __init__(self):
        # หาก URL การเชื่อมต่อระบุเป็น postgresql:// (sync) ให้สลับเป็น postgresql+asyncpg:// (async) อัตโนมัติเพื่อใช้ร่วมกับ SQLAlchemy Async
        if self.SUPABASE_DB_URL.startswith("postgresql://"):
            self.SUPABASE_DB_URL = self.SUPABASE_DB_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

settings = Settings()


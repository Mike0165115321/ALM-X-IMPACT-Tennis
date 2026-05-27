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

    # SMS Settings
    SMS_API_KEY: str = os.getenv("SMS_API_KEY", "")
    SMS_API_SECRET: str = os.getenv("SMS_API_SECRET", "")
    SMS_SENDER_NAME: str = os.getenv("SMS_SENDER_NAME", "SMS")

settings = Settings()

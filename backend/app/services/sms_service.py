import httpx
import logging
from app.config import settings

logger = logging.getLogger("sms_service")

class SMSService:
    @staticmethod
    async def send_otp_sms(phone: str, otp_code: str, ref_code: str) -> bool:
        """
        ส่ง SMS OTP ผ่านทางเครือข่าย ThaiBulkSMS
        หากไม่มีการระบุ SMS_API_KEY หรือ SMS_API_SECRET ใน .env 
        จะทำการรันโหมดจำลอง (Simulator) อัตโนมัติ เพื่อป้องกันระบบ Error
        """
        # 1. ตรวจสอบว่าเปิดโหมดใช้งานจริงหรือไม่
        if not settings.SMS_API_KEY or not settings.SMS_API_SECRET:
            logger.info("⚠️ [SMS API SIMULATOR MODE - NO API KEY]")
            print(f"🔥 [SMS OTP SIMULATOR] Sent OTP: {otp_code} (Ref: {ref_code}) to {phone}")
            return True

        # 2. ปรับเบอร์ไทยให้อยู่ในฟอร์แมตสากล (เช่น 0812345678 -> 66812345678)
        formatted_phone = phone
        if phone.startswith("0"):
            formatted_phone = "66" + phone[1:]

        api_url = "https://api-v2.thaibulksms.com/sms"
        
        # 3. ตกแต่งข้อความ SMS
        message = f"รหัส OTP ของคุณคือ {otp_code} (Ref: {ref_code}) สำหรับจองสนามเทนนิส IMPACT (หมดอายุใน 5 นาที)"

        payload = {
            "msisdn": formatted_phone,
            "message": message,
            "sender": settings.SMS_SENDER_NAME,
            "force": "standard"
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        # ThaiBulkSMS ใช้การ Auth ด้วย Basic Authentication (API_KEY, API_SECRET)
        auth = (settings.SMS_API_KEY, settings.SMS_API_SECRET)

        try:
            logger.info(f"📲 กำลังส่ง SMS OTP ไปยัง {phone} ผ่าน ThaiBulkSMS...")
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    api_url, 
                    data=payload, 
                    headers=headers, 
                    auth=auth, 
                    timeout=10.0
                )
                
                if response.status_code in [200, 201]:
                    logger.info(f"✅ ส่ง SMS สำเร็จไปยังเบอร์ {phone}!")
                    return True
                else:
                    logger.error(f"❌ SMS Gateway ตอบกลับผิดพลาด (HTTP {response.status_code}): {response.text}")
                    return False
        except Exception as e:
            logger.error(f"❌ เกิดข้อผิดพลาดทางเทคนิคขณะส่ง SMS: {str(e)}")
            return False

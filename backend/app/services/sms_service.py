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

        # สำหรับ OTP API v1 ของ ThaiBulkSMS จะยิงไปที่ https://otp.thaibulksms.com/v1/otp/request
        # โดยการส่ง Parameter ผ่าน Query String (หรือ URL encoded)
        api_url = "https://otp.thaibulksms.com/v1/otp/request"
        
        params = {
            "key": settings.SMS_API_KEY,
            "secret": settings.SMS_API_SECRET,
            "msisdn": formatted_phone
        }

        try:
            logger.info(f"📲 กำลังยิงคำขอ OTP ไปยังเบอร์ {phone} ผ่าน OTP Gateway...")
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    api_url, 
                    params=params,
                    timeout=10.0
                )
                
                if response.status_code in [200, 201]:
                    res_data = response.json()
                    # ตรวจสอบการตอบกลับผิดพลาดของ API ภายใน JSON
                    if res_data.get("status") == "success" or "data" in res_data:
                        # บันทึก token สำหรับเอาไว้ตรวจสอบการยืนยันภายหลัง
                        token = res_data["data"]["token"]
                        logger.info(f"✅ ส่งคำขอ OTP สำเร็จ! (Token: {token})")
                        
                        # เพื่อให้ระบบ mock_db สามารถทำต่อระบบตรวจสอบรหัสเองได้แบบอิงจริง
                        # เราเก็บ token นี้เข้าคู่เบอร์โทรศัพท์ไว้ใน mock_otp_store
                        from app.services.mock_db import mock_otp_store
                        if phone in mock_otp_store:
                            mock_otp_store[phone]["otp_token"] = token
                            
                        return True
                    else:
                        error_msg = res_data.get("errors", {}).get("message", "Unknown error")
                        logger.error(f"❌ OTP API Response Error: {error_msg}")
                        return False
                else:
                    logger.error(f"❌ OTP Gateway ตอบกลับผิดพลาด (HTTP {response.status_code}): {response.text}")
                    return False
        except Exception as e:
            logger.error(f"❌ เกิดข้อผิดพลาดขณะยิง OTP API: {str(e)}")
            return False

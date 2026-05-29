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

        # ดึง URL ปลายทางของ API มาจากไฟล์คอนฟิก
        base_otp_url = settings.SMS_OTP_API_URL
        api_url = f"{base_otp_url}/request"
        
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
                    if res_data.get("status") == "success" or "data" in res_data:
                        token = res_data["data"]["token"]
                        logger.info(f"✅ ส่งคำขอ OTP สำเร็จ! (Token: {token})")
                        
                        from app.services.otp_store import otp_store
                        if phone in otp_store:
                            otp_store[phone]["otp_token"] = token
                            
                        return True
                    else:
                        error_msg = res_data.get("errors", {}).get("message", "Unknown error")
                        logger.error(f"❌ OTP API Response Error: {error_msg}")
                        return False
                else:
                    logger.error(f"❌ OTP Gateway ตอบกลับผิดพลาด (HTTP {response.status_code}): {response.text}")
                    return False
        except httpx.RequestError as exc:
            logger.error(f"❌ [Network Error] ไม่สามารถเชื่อมต่อกับ SMS Gateway ได้: {exc}")
            from app.exceptions import SMSGatewayException
            raise SMSGatewayException(f"เกิดข้อผิดพลาดในการติดต่อกับบริการส่ง SMS ภายนอก: {str(exc)}")
        except Exception as e:
            logger.error(f"❌ [System Error] เกิดข้อผิดพลาดไม่ทราบสาเหตุขณะยิง OTP API: {str(e)}")
            return False

    @staticmethod
    async def verify_otp_via_api(phone: str, otp_code: str, otp_token: str) -> bool:
        """
        ตรวจสอบความถูกต้องของ OTP ผ่าน API ThaiBulkSMS จริง (Async)
        """
        api_url = "https://otp.thaibulksms.com/v1/otp/verify"
        
        params = {
            "key": settings.SMS_API_KEY,
            "secret": settings.SMS_API_SECRET,
            "token": otp_token,
            "pin": otp_code
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    api_url,
                    params=params,
                    timeout=10.0
                )
                
                if response.status_code in [200, 201]:
                    res_data = response.json()
                    # หากตอบกลับเป็น success หรือ status 'success' ยืนยันตัวตนสำเร็จ
                    if res_data.get("status") == "success" or res_data.get("data", {}).get("status") == "success":
                        return True
            return False
        except httpx.RequestError as exc:
            logger.error(f"❌ [Network Error] ไม่สามารถยืนยัน OTP กับ SMS Gateway ได้: {exc}")
            from app.exceptions import SMSGatewayException
            raise SMSGatewayException(f"ไม่สามารถเช็คยืนยัน OTP กับระบบภายนอกได้ชั่วคราว: {str(exc)}")
        except Exception as e:
            logger.error(f"❌ [System Error] เกิดข้อผิดพลาดในระบบตรวจรหัส OTP: {str(e)}")
            return False


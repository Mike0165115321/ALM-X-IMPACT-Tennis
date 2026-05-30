import httpx
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("easyslip_service")

class EasySlipService:
    """
    บริการตรวจสอบสลิปอัตโนมัติผ่าน EasySlip API v2
    """
    BASE_URL = "https://api.easyslip.com/v2"

    @classmethod
    async def verify_slip(cls, api_key: str, qr_payload: str, expected_amount: float) -> Dict[str, Any]:
        """
        ยิงข้อมูลตรวจสลิปโอนเงินผ่าน API v2 ของ EasySlip
        """
        if not api_key:
            logger.warning("⚠️ ไม่มี API Key ของ EasySlip - ข้ามระบบการตรวจสอบจริง")
            return {"success": False, "error_message": "EASYSLIP_API_KEY is not configured"}

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "payload": qr_payload,
            "matchAmount": expected_amount
        }

        try:
            logger.info(f"🌐 กำลังยิงข้อมูลตรวจสลิปไปที่ EasySlip สำหรับยอด {expected_amount} บาท...")
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{cls.BASE_URL}/verify/bank",
                    json=payload,
                    headers=headers
                )
                
                # หากเชื่อมต่อหรือรับส่งสำเร็จ
                res_data = response.json()
                if response.status_code == 200 and res_data.get("success") is True:
                    logger.info("✅ ตรวจสอบสลิปผ่าน EasySlip สำเร็จ!")
                    return {
                        "success": True,
                        "amount_in_slip": res_data["data"].get("amountInSlip"),
                        "is_amount_matched": res_data["data"].get("isAmountMatched", False),
                        "raw_data": res_data["data"]
                    }
                else:
                    err_msg = res_data.get("error", {}).get("message", "Unknown error")
                    logger.error(f"❌ EasySlip ตอบกลับมาว่าไม่สำเร็จ: {err_msg}")
                    return {"success": False, "error_message": err_msg}

        except Exception as e:
            logger.error(f"❌ เกิดข้อผิดพลาดในการเชื่อมต่อกับ EasySlip: {str(e)}")
            return {"success": False, "error_message": str(e)}

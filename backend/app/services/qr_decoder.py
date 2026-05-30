import os
import logging
from PIL import Image
# pyrefly: ignore [missing-import]
from pyzbar.pyzbar import decode
from typing import Optional

logger = logging.getLogger("qr_decoder")

class QRDecoder:
    """
    ถอดรหัส Mini-QR Code จากรูปภาพสลิปโอนเงินธนาคาร
    """
    @staticmethod
    def decode_qr(file_path: str) -> Optional[str]:
        """
        อ่านข้อมูล QR Code จากรูปภาพต้นทางแบบโลคอล
        """
        if not os.path.exists(file_path):
            logger.error(f"❌ ไม่พบรูปภาพที่ระบุ: {file_path}")
            return None

        try:
            # เปิดรูปภาพด้วย Pillow
            img = Image.open(file_path)
            # ถอดรหัสบาร์โค้ดและ QR Code ทั้งหมดในภาพ
            decoded_objects = decode(img)
            
            for obj in decoded_objects:
                # ดึงค่า QR Payload ออกมาแปลงเป็น String
                qr_data = obj.data.decode("utf-8")
                if qr_data:
                    logger.info(f"✅ ถอดรหัส QR Code สำเร็จ: {qr_data[:30]}...")
                    return qr_data
                    
            logger.warning(f"⚠️ ไม่พบรหัส QR Code ใดๆ ในรูปภาพ: {file_path}")
            return None
        except Exception as e:
            logger.error(f"❌ เกิดข้อผิดพลาดขณะอ่านหรือประมวลผล QR Code: {str(e)}")
            return None

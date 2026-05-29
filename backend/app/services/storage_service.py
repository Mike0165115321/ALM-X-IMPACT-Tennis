import os
import shutil
import uuid
import asyncio
from datetime import datetime, timezone
from fastapi import UploadFile, Request, HTTPException, status

class StorageService:
    """
    ระบบบริการจัดการไฟล์อัปโหลด (Storage Service Simulator)
    ออกแบบมารองรับการเปลี่ยนผ่านไปใช้งาน Google Cloud Storage หรือ AWS S3 ในอนาคต
    โดยที่จุดเรียกใช้งานอื่นๆ ใน Router จะไม่ต้องแก้ไขใดๆ เลย
    """
    
    UPLOAD_DIR = "uploads"
    
    @classmethod
    def init_app(cls, app):
        """
        ตั้งค่าเริ่มต้นสำหรับระบบจัดเก็บไฟล์ในแอปพลิเคชัน (FastAPI app)
        ในโหมดจำลองนี้ จะทำการสร้างโฟลเดอร์สำหรับเก็บไฟล์โลคอล และทำการ mount static files path
        หากย้ายไปคลาวด์จริงในอนาคต สามารถเขียนเงื่อนไขปิดการใช้หรือสลับไปใช้ Cloud SDK setup ที่นี่ได้เลย
        """
        from fastapi.staticfiles import StaticFiles
        os.makedirs(cls.UPLOAD_DIR, exist_ok=True)
        app.mount(f"/{cls.UPLOAD_DIR}", StaticFiles(directory=cls.UPLOAD_DIR), name="uploads")

    
    @classmethod
    async def upload_slip(cls, slip_file: UploadFile, booking_id: str, request: Request) -> str:
        """
        อัปโหลดภาพสลิปโอนเงิน (จำลองแบบเก็บลงดิสก์เครื่องโลคอล) แบบ Async (C7)
        """
        # 1. ตรวจสอบนามสกุลไฟล์
        if not slip_file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="กรุณาอัปโหลดไฟล์รูปภาพสลิปที่ถูกต้อง (PNG, JPG, JPEG, WEBP)"
            )
            
        # 2. ตรวจสอบให้มั่นใจว่าสร้างโฟลเดอร์สำหรับเก็บสลิปอัปโหลดแล้ว
        os.makedirs(cls.UPLOAD_DIR, exist_ok=True)
        
        # 3. สร้างชื่อไฟล์ที่ไม่ซ้ำกันเพื่อความปลอดภัยและป้องกันการเขียนทับ
        ext = os.path.splitext(slip_file.filename)[1]
        unique_filename = f"{booking_id}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}{ext}"
        file_path = os.path.join(cls.UPLOAD_DIR, unique_filename)
        
        # 4. เขียนข้อมูลไฟล์รูปภาพลงในดิสก์แบบ Non-blocking IO โดยใช้ asyncio.to_thread() (C7)
        def save_file():
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(slip_file.file, buffer)

        try:
            await asyncio.to_thread(save_file)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"เกิดข้อผิดพลาดในการบันทึกไฟล์สลิปเข้าระบบหลังบ้าน: {str(e)}"
            )
            
        # 5. ดึงและประกอบ Base URL แบบไดนามิกเพื่อส่งกลับไปยัง Client
        base_url = str(request.base_url)
        return f"{base_url}{cls.UPLOAD_DIR}/{unique_filename}"

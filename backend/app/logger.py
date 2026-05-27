import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    """
    ตั้งค่าระบบการบันทึก Log ของแอปพลิเคชันอย่างเป็นระบบ
    - แสดงข้อความบน Console สำหรับการพัฒนา (Developer Console)
    - บันทึกรายละเอียด Log ทั้งหมดลงในไฟล์ logs/app.log อัตโนมัติ (และมีระบบสลับไฟล์อัตโนมัติหากเกิน 5MB)
    """
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
    )

    # 1. File Logger (หมุนสลับไฟล์ขนาดสูงสุด 5MB, เก็บสำรองไว้ 5 ไฟล์)
    log_file = os.path.join(log_dir, "app.log")
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(logging.INFO)

    # 2. Console Logger
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(logging.INFO)

    # ดึง Root Logger มาตั้งค่า
    root_logger = logging.getLogger()
    
    # ล้าง Handler เก่าออกก่อนป้องกันการแสดงผลซ้ำซ้อน
    if root_logger.handlers:
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    logging.getLogger("uvicorn.error").addHandler(file_handler)
    logging.getLogger("uvicorn.access").addHandler(file_handler)

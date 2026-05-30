import os
import sys
import asyncio
import logging
from PIL import Image

# ปรับเพื่อให้สามารถ import app/services ได้ตรงๆ
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))

from app.config import settings
from app.services.qr_decoder import QRDecoder
from app.services.easyslip_service import EasySlipService

# ตั้งค่า Logging ให้เห็นรายละเอียดชัดเจน
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

async def main():
    print("==========================================================")
    print("      EasySlip V2 Real-Time Verification CLI Tester       ")
    print("==========================================================")
    
    # 1. ตรวจสอบ API Key
    api_key = settings.EASYSLIP_API_KEY
    if not api_key:
        print("[ERROR] EASYSLIP_API_KEY is not set in backend/.env file!")
        return

    print(f"[INFO] Using API Key: {api_key[:8]}...{api_key[-8:] if len(api_key) > 8 else ''}")

    # 2. หารูปภาพสลิปสำหรับการทดสอบ
    # รับชื่อไฟล์จาก command-line arguments หรือใช้ค่าเริ่มต้น
    slip_filename = "real_slip.png"
    if len(sys.argv) > 1:
        slip_filename = sys.argv[1]

    expected_amount = 300.0
    if len(sys.argv) > 2:
        try:
            expected_amount = float(sys.argv[2])
        except ValueError:
            print(f"[WARN] Invalid expected amount. Using default: {expected_amount} THB")

    file_path = os.path.join(os.path.dirname(__file__), slip_filename)
    
    if not os.path.exists(file_path):
        print(f"[ERROR] Target slip image not found at: {file_path}")
        print("Please place a real bank transfer slip (with Mini-QR code) inside the backend/ folder")
        print(f"and name it '{slip_filename}' (or pass its name as the first argument).")
        print("\nExample: python verify_real_slip.py my_slip.jpg 350.0")
        print("==========================================================")
        return

    print(f"[INFO] Loading slip image: {file_path}")
    print(f"[INFO] Expected verification amount: {expected_amount} THB")
    
    # 3. ถอดรหัส QR Payload โลคอล
    print("[STEP 1/3] Decoding Mini-QR code payload from image...")
    try:
        qr_payload = QRDecoder.decode_qr(file_path)
    except Exception as e:
        print(f"[ERROR] QR Decoder failed: {str(e)}")
        return

    if not qr_payload:
        print("[ERROR] Failed to extract any QR Payload or Mini-QR code from the image.")
        print("Please ensure the slip image contains a clear, un-cropped bank QR code.")
        return

    print(f"[SUCCESS] Decoded QR Payload: {qr_payload}")

    # 4. เรียกใช้งาน EasySlip API v2 ของจริง
    print("[STEP 2/3] Calling EasySlip API v2 to verify the QR Payload...")
    res = await EasySlipService.verify_slip(
        api_key=api_key,
        qr_payload=qr_payload,
        expected_amount=expected_amount
    )

    print("==========================================================")
    print("                     VERIFICATION RESULT                  ")
    print("==========================================================")
    
    if res.get("success") is True:
        print("[STATUS] Verification SUCCESS!")
        print(f"[DATA] Sender: {res['raw_data'].get('sender', {}).get('displayName', 'N/A')}")
        print(f"[DATA] Receiver: {res['raw_data'].get('receiver', {}).get('displayName', 'N/A')}")
        print(f"[DATA] Transferred Amount: {res.get('amount_in_slip')} THB")
        print(f"[DATA] Expected Amount: {expected_amount} THB")
        print(f"[DATA] Amount Matched: {res.get('is_amount_matched')}")
        print(f"[DATA] Bank Ref/Transaction ID: {res['raw_data'].get('transRef', 'N/A')}")
        print(f"[DATA] Transaction Date/Time: {res['raw_data'].get('transDate')} {res['raw_data'].get('transTime')}")
        
        if res.get('is_amount_matched') is True:
            print("\n>>> [DECISION] AUTO-APPROVE: Yes! Booking status can be safely transition to 'confirmed'!")
        else:
            print("\n>>> [WARN] [DECISION] REJECT/PENDING: Amount mismatch. Admin review required.")
    else:
        print("[STATUS] Verification FAILED!")
        print(f"[ERROR] Reason: {res.get('error_message')}")
        
    print("==========================================================")
    print("[INFO] Try checking your EasySlip dashboard. The 'Verified' request count should have incremented!")
    print("==========================================================")

if __name__ == "__main__":
    asyncio.run(main())

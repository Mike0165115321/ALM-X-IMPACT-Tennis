"""
In-memory OTP Store (Ephemeral — รีเซ็ตเมื่อ restart server)
แยกออกมาเป็นโมดูลเฉพาะเพื่อหลีกเลี่ยง Circular Import ระหว่าง data_service ↔ sms_service

Format: {phone: {otp_code, ref_code, created_at, request_count, last_request_at, otp_token}}
"""
from typing import Dict, Any

otp_store: Dict[str, Dict[str, Any]] = {}

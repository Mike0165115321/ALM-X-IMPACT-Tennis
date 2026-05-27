import csv
import json
import os
import sys
import uuid
from datetime import datetime

# เพิ่มพาธ backend เข้ามาใน sys.path เพื่อให้สามารถเรียกใช้ฟังก์ชัน hash_password ได้
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

try:
    # pyrefly: ignore [missing-import]
    from app.utils import hash_password
except ImportError:
    # Fallback ในกรณีรันสคริปต์แยกจากโฟลเดอร์อื่น
    def hash_password(password: str) -> str:
        # ส่งค่าจำลองกลับไปหากหาไลบรารีไม่เจอ
        return f"$2b$12$fakehashplaceholderforpassword_{password}"

def clean_phone(phone_raw: str) -> str:
    """
    ล้างข้อมูลเบอร์โทรศัพท์ ดึงอักขระที่เป็นตัวเลขออก และเติม 0 นำหน้าให้เป็นเบอร์ไทย 10 หลัก
    """
    if not phone_raw:
        return ""
    # เอาอักขระที่ไม่ใช่ตัวเลขออก
    cleaned = "".join(c for c in phone_raw if c.isdigit())
    if not cleaned:
        return ""
    
    # หากยาว 9 หลัก (เช่น 809132580) ให้เติม 0 ไปข้างหน้า
    if len(cleaned) == 9:
        cleaned = "0" + cleaned
        
    return cleaned

def convert_buddhist_year(date_str: str) -> str:
    """
    แปลงวันที่ พ.ศ. (D/M/YYYY) เป็นปี ค.ศ. (YYYY-MM-DD)
    """
    if not date_str or date_str.lower() in ["", "null"]:
        return ""
    
    try:
        # ตัดแบ่ง วัน/เดือน/ปีพ.ศ.
        parts = date_str.split("/")
        if len(parts) != 3:
            return date_str
            
        day = int(parts[0])
        month = int(parts[1])
        year_be = int(parts[2])
        
        # แปลง พ.ศ. -> ค.ศ.
        year_ad = year_be - 543
        
        # ส่งกลับฟอร์แมต YYYY-MM-DD
        return f"{year_ad:04d}-{month:02d}-{day:02d}"
    except Exception:
        return date_str

def main():
    csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "ALM_Users Demographic.csv"))
    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "app", "services", "seeded_users.json"))
    
    print(f"Reading CSV file from: {csv_path}")
    
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found!")
        sys.exit(1)
        
    seeded_users = {}
    
    # กำหนด password hash เริ่มต้นสำหรับทุกคนคือ "welcome123"
    print("Generating default password hash for all users ('welcome123')...")
    default_hashed_password = hash_password("welcome123")
    
    with open(csv_path, mode="r", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        
        count = 0
        for row in reader:
            user_id = row.get("User ID")
            if not user_id:
                user_id = str(uuid.uuid4())
                
            username = row.get("ชื่อเล่น")
            if not username or username.strip() == "":
                username = row.get("ชื่อ")
                
            # ล้างค่าเบอร์โทรศัพท์และวันที่สมัคร
            phone = clean_phone(row.get("เบอร์โทร", ""))
            created_at_ad = convert_buddhist_year(row.get("วันที่สมัคร", ""))
            
            # กำหนดสิทธิ์บทบาท (Role)
            role = "player"
            if row.get("อีเมล") == "managingdirector@kfd.co.th":
                role = "admin" # ผู้ใช้ที่เป็น MD เก่าให้สิทธิ์เป็น Admin ติดตัวไป
            
            user_doc = {
                "id": user_id,
                "username": username,
                "email": row.get("อีเมล", ""),
                "password_hash": default_hashed_password,
                "google_id": None,
                "role": role,
                "profile": {
                    "display_name": f"{row.get('ชื่อ', '')} {row.get('นามสกุล', '')}".strip(),
                    "phone": phone,
                    "is_phone_verified": row.get("สถานะยืนยันตัวตน", "").lower() == "approved",
                    "ntrp_rating": 1.5, # ค่าเริ่มต้นระดับฝีมือเทนนิส
                    "wtn_rating": 40.0,
                    "playing_style": "All-Court",
                    "match_preference": "any",
                    "gender": row.get("เพศ", "").lower(),
                    "birthday": row.get("วันเกิด", ""),
                    "nationality": row.get("สัญชาติ", "").lower(),
                    "vip": row.get("VIP", "").lower() == "yes",
                    "points": int(row.get("Point สะสม", "0").replace(",", "") or 0)
                },
                "created_at": created_at_ad
            }
            
            seeded_users[user_id] = user_doc
            count += 1
            
    print(f"Writing {count} users to JSON file...")
    
    # มั่นใจว่ามีโฟลเดอร์สำหรับเขียนไฟล์ผลลัพธ์
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as out_file:
        json.dump(seeded_users, out_file, indent=2, ensure_ascii=False)
        
    print(f"Success! Seeded users written to {output_path}")

if __name__ == "__main__":
    main()

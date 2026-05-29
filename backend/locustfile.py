import random
import uuid
# pyrefly: ignore [missing-import]
from locust import HttpUser, task, between

class TennisAppUser(HttpUser):
    # จำลองเวลาหน่วงในการตัดสินใจของแต่ละคนระหว่าง 0.5 ถึง 2.0 วินาที
    wait_time = between(0.5, 2.0)
    
    def on_start(self):
        """
        ทำงานเมื่อบอทแต่ละตัวถูกสร้างขึ้น
        ทำการลงทะเบียนและเข้าสู่ระบบเพื่อรับสิทธิ์ JWT Token ไปใช้ในภารกิจอื่น ๆ
        """
        self.username = f"locust_user_{uuid.uuid4().hex[:8]}"
        self.email = f"{self.username}@locust-test.com"
        self.password = "supersecurepassword123"
        self.phone = f"087{random.randint(1000000, 9999999)}"
        self.auth_headers = {}
        
        # 1. 👥 จำลองการสมัครสมาชิก
        reg_payload = {
            "username": self.username,
            "email": self.email,
            "password": self.password,
            "phone": self.phone
        }
        
        with self.client.post("/api/v1/auth/register", json=reg_payload, catch_response=True) as response:
            if response.status_code == 201:
                data = response.json()
                self.token = data.get("access_token")
                self.auth_headers = {"Authorization": f"Bearer {self.token}"}
                response.success()
            else:
                response.failure(f"Registration failed: {response.text}")

    @task(3)
    def view_courts_directory(self):
        """
        ฟลูเวิร์กโฟลว์การดึงรายชื่อสนามและเช็กสถานะสล็อตว่าง (ผู้ใช้รุมเปิดดูบ่อยที่สุด)
        """
        random_date = f"2026-06-{random.randint(10, 28)}"
        with self.client.get(f"/api/v1/courts?date={random_date}", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to fetch courts: {response.status_code}")

    @task(2)
    def find_player_matchmaking(self):
        """
        ฟลูเวิร์กโฟลว์การดึงคู่แมตช์ที่เข้าเกณฑ์ระดับ NTRP (คำนวณและประมวลผลสูง)
        """
        if not self.auth_headers:
            return  # ข้ามหากสมัครสมาชิกไม่ผ่าน
            
        payload = {
            "court_id": "9a0c4ee1-f9fe-4bbb-8bdc-9407e08c0763", # ID สนามทดสอบ
            "match_date": "2026-06-15",
            "time_slot": "16:00-17:00",
            "match_type": "singles",
            "ntrp_min": 1.5,
            "ntrp_max": 4.5,
            "preferred_playing_style": "All-Court"
        }
        
        with self.client.post("/api/v1/matching/find", json=payload, headers=self.auth_headers, catch_response=True) as response:
            # ยอมรับ HTTP 200 (สำเร็จ) หรือ HTTP 400 (เช่น กรณีโดน Guard บล็อกเพราะยังไม่ยืนยัน OTP เบอร์โทรศัพท์)
            # ถือว่าโค้ด FastAPI จัดการดักเคสความปลอดภัยได้อย่างมั่นคง ไม่แตกพัง
            if response.status_code in [200, 400]:
                response.success()
            else:
                response.failure(f"Matchmaking API returned error {response.status_code}: {response.text}")

    @task(1)
    def get_dashboard_general_data(self):
        """
        ฟลูเวิร์กโฟลว์การเปิดดูหน้าโฮมเพจหลักเพื่อแสดงภาพรวม
        """
        with self.client.get("/api/v1/data", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to fetch dashboard data: {response.status_code}")

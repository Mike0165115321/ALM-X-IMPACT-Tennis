FROM python:3.11-slim

# ตั้งค่า working directory ในคอนเทนเนอร์
WORKDIR /app

# คัดลอกเฉพาะไฟล์ dependencies เพื่อความรวดเร็วในการบิวต์แคช
COPY requirements.txt .

# ติดตั้งไลบรารีทั้งหมดโดยไม่มีการเก็บแคชเพื่อลดขนาดอิมเมจ
RUN pip install --no-cache-dir -r requirements.txt

# คัดลอกโค้ดระบบหลังบ้านทั้งหมดเข้ามา
COPY . .

# เปิดพอร์ตสำหรับให้บริการ API
EXPOSE 8000

# สตาร์ทเซิร์ฟเวอร์ด้วย uvicorn ให้ผูกไอพีรับทุกช่องทางภายนอก
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

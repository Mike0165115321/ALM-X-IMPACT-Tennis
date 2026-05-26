# 🎾 ALM-X-IMPACT Tennis 🎾
> **ระบบจองคิวสนามเทนนิส และระบบหาคู่เล่นอัจฉริยะ (NTRP-Based Matchmaking System)**
> พัฒนาภายใต้สถาปัตยกรรม Mono-Repo สำหรับทีมงาน ALM Impact Tennis

---

## 📑 เอกสารอ้างอิงโครงการ (Project Documentation)
ก่อนเริ่มลงมือเขียนโค้ด ขอความร่วมมือสมาชิกในทีมทุกคนอ่านเอกสารกลางเหล่านี้เพื่อรักษามาตรฐานเดียวกัน:
*   **[เอกสารกลางสเปกโครงการ (Project Specification)](docs/project_specification.md)** - สถาปัตยกรรม, เวอร์ชัน, คู่มือความเข้ากันได้, Schema ฐานข้อมูล และสัญญาข้อตกลง API
*   **[ข้อกำหนดฟีเจอร์หลัก (Core Features Spec)](docs/core%20feature.md)** - ขอบเขตระบบ MVP, Flow การทำงานของลูกค้า, เกณฑ์ระดับฝีมือ NTRP/WTN และแผนงานของแมตช์

---

## 🛠️ Tech Stack & Local Ports
โครงการนี้ใช้เทคโนโลยีเวอร์ชันล่าสุด เสถียร และมีประสิทธิภาพสูงสุด โดยกำหนดพอร์ตในการทดสอบบนเครื่องดังนี้:

| ส่วนงาน | เทคโนโลยี | เวอร์ชันที่กำหนด | URL / Port ท้องถิ่น |
| :--- | :--- | :--- | :--- |
| **หน้าบ้าน (Frontend)** | Wix.com | - | เชื่อมต่อผ่าน API |
| **หลังบ้าน (Backend)** | Python (FastAPI), Uvicorn, Beanie ODM | `Python 3.11.9` | `http://localhost:8000` |
| **ฐานข้อมูล (Database)** | MongoDB Community Server | `MongoDB v7.0.9` | `mongodb://localhost:27017` |

---

## 📂 โครงสร้างโฟลเดอร์ (Directory Structure)
```text
ALM-X-IMPACT-Tennis/
├── docs/                 # เอกสารสเปกโครงการและการวิเคราะห์ฟีเจอร์
├── backend/              # หลังบ้านพัฒนาด้วย Python FastAPI + MongoDB (เชื่อมต่อกับ Wix.com)
└── database/             # Scripts สำหรับ Seed data และ Config ทั่วไป
```

---

## 🚀 คู่มือการเริ่มใช้งานด่วนสำหรับทีมพัฒนา (Quick Start Guide)

### 💻 1. การเตรียมสภาพแวดล้อม (Prerequisites)
ตรวจสอบให้แน่ใจว่าเครื่องคอมพิวเตอร์ของคุณลงโปรแกรมเหล่านี้ตามเวอร์ชันของเครื่องพัฒนาหลัก:
*   **Python:** เวอร์ชัน `v3.11.9` (เช็กด้วย `python --version`)
*   **MongoDB:** ติดตั้ง MongoDB Community Server และเปิดรันที่พอร์ต `27017`

---

### 🐍 2. การตั้งค่าฝั่งหลังบ้าน (Backend Setup)
1. ไปยังโฟลเดอร์ backend:
   ```bash
   cd backend
   ```
2. สร้างและใช้งาน Virtual Environment (เพื่อความเป็นระเบียบของแพ็คเกจ):
   ```bash
   python -m venv venv
   # สำหรับ Windows (PowerShell):
   .\venv\Scripts\Activate.ps1
   # สำหรับ Mac/Linux:
   source venv/bin/activate
   ```
3. ติดตั้งไลบรารีที่ระบุในข้อตกลง:
   ```bash
   pip install -r requirements.txt
   ```
4. รัน FastAPI Server ด้วย Uvicorn:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
5. เข้าดูหน้าทดสอบระบบและ Swagger API Docs ที่: `http://localhost:8000/docs`

---

## 🌿 กฎการร่วมงาน Git & Branching Rules
เพื่อให้ประวัติประมวลผลโค้ดของทีมสะอาดและไม่พังเลอะเทอะ ขอให้ทำตามกฎนี้:

### 🎋 1. การตั้งชื่อกิ่ง (Branch Naming)
*   `main` : กิ่งโปรดักชันห้าม Push ตรง ๆ ทุกกรณี (ต้องผ่าน Pull Request และรีวิวเท่านั้น)
*   `develop` : กิ่งรวมงานหลักสำหรับนักพัฒนาเพื่อรัน Staging Test
*   `feature/ชื่อฟีเจอร์` : สำหรับงานฟีเจอร์ใหม่ เช่น `feature/google-login`, `feature/ntrp-filter`
*   `bugfix/ชื่อบั๊ก` : สำหรับการแก้ไขบั๊กทั่วไป เช่น `bugfix/fix-otp-timeout`
*   `hotfix/ด่วน` : สำหรับแก้บั๊กร้ายแรงเร่งด่วนบน Production

### ✍️ 2. Commit Message (Conventional Commits)
เขียนข้อความให้เป็นระบบเพื่อความง่ายในการอ่านย้อนหลัง เช่น:
*   `feat: add google oauth endpoint` (เพิ่มฟีเจอร์ใหม่)
*   `fix: resolve passlib bcrypt python 3.11 crash` (แก้ข้อผิดพลาด)
*   `docs: update readme with quickstart guides` (เพิ่มเอกสารประกอบ)

---

> 🎾 **Let's Make Tennis Great Again!**
> หากมีข้อสงสัยหรือเจอปัญหาขัดข้องทางเทคนิค กรุณาลงโน้ตคุยกันในช่องทาง Discord / Line ของกลุ่มทีมงาน หรือเขียนคำถามไว้ในแท็บ Issue บน GitHub ของกลุ่มพวกเราครับ!

import smtplib
import logging
import asyncio
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.config import settings

logger = logging.getLogger("email_service")

class EmailService:
    @staticmethod
    def _send_smtp_sync(to_email: str, subject: str, body_html: str) -> bool:
        """
        ฟังก์ชัน Synchronous สำหรับเชื่อมต่อ SMTP และส่งอีเมลผ่าน TLS (เช่น Hotmail/Outlook)
        """
        if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
            logger.info("⚠️ [EMAIL SMTP SIMULATOR MODE - NO SMTP CREDENTIALS]")
            print(f"🔥 [EMAIL SIMULATOR] Sent Email to {to_email}\nSubject: {subject}\nContent: {body_html[:200]}...")
            return True

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f'"{settings.SMTP_FROM_NAME}" <{settings.SMTP_USERNAME}>'
        msg["To"] = to_email

        # แปะเนื้อหาแบบ HTML
        html_part = MIMEText(body_html, "html", "utf-8")
        msg.attach(html_part)

        try:
            logger.info(f"📧 กำลังส่งอีเมลผ่าน SMTP Hotmail ไปยัง {to_email}...")
            # สำหรับพอร์ต 587 ต้องเริ่มต้นแบบเชื่อมต่อธรรมดาแล้วสั่ง STARTTLS
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15)
            server.ehlo()
            server.starttls()
            server.ehlo()
            
            # ล็อกอินด้วยอีเมลบริษัทและ App Password
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            
            # ส่งเมล
            server.sendmail(settings.SMTP_USERNAME, to_email, msg.as_string())
            server.quit()
            logger.info(f"✅ ส่งอีเมลไปยัง {to_email} สำเร็จเรียบร้อย!")
            return True
        except Exception as e:
            logger.error(f"❌ เกิดข้อผิดพลาดในการส่งอีเมลผ่าน SMTP: {str(e)}")
            return False

    @classmethod
    async def send_email(cls, to_email: str, subject: str, body_html: str) -> bool:
        """
        ฟังก์ชัน Asynchronous สำหรับเรียกใช้งานส่งอีเมลแบบ Non-blocking IO
        โดยการโยนงาน Sync ไปรันใน Thread Pool เพื่อไม่ทำให้เซิร์ฟเวอร์ค้าง
        """
        return await asyncio.to_thread(cls._send_smtp_sync, to_email, subject, body_html)

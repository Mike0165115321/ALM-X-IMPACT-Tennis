Core Feature 

core feature Booking + Matching คู่เล่นเทนนิสตามความเก่ง ให้ดูพวก NTRP เป็นหลัก และสามารถ customize ได้ตามความชอบของผู้เล่นเอง เช่น ผู้เล่นชอบเจอคนเก่งเท่ากัน คนเก่งมากกว่า หรือคนเก่งน้อยกว่าตัวเองเป็นต้น

Feature ที่ต้องมี (MVP)
-Booking + Matching system
-มีระบบชำระเงินให้ (ตัวอย่าง)
-ระบบ login ด้วย Google เพื่อให้คนสมัคร
-ในหน้าหลักมีเขียนถึง vision ของ alm impact tennis
-มี FAQ section
-มี Contact section

Flow
คนเปิดเว็บ > คนอยากจองสนาม > คนกดจอง > คนเชื่อม gmail ตัวเอง > ยืนยันเบอร์โทร OTP > กรอกระดับ NTRP ของตัวเองและกรอกว่าต้องการเจอผู้เล่น NTRP ระดับไหนบ้าง > workflow ไปสืบมาว่า ใครที่ตรงกับ requriement ของ users ก็ดึงมาให้มา Match กัน > หลัง match กันแล้ว ให้ผู้เล่นนัดวันและเวลามาเล่นกันได้ > มีการมาเจอกัน เล่นด้วยกัน > **คนสนุกชอบจะทำการรีวิว (UGC Content)**

Example website
https://tennispal.com/ (ลองโหลดมาใช้หรือลองดูรีวิว) เพื่อดู flow การทำงานและ UI 
add on 
ฟีเจอร์ Matching ที่ควรมี (เพื่อให้เจ๋งและ usable)
●	Core Matching: Filter ตาม rating (NTRP 1.5-7.0 หรือ WTN 40-1), distance, time, singles/doubles, preferred playing style. แนะนำ "compatible matches" แบบ algorithm.
●	Verification & Trust: Self-rate + optional video upload, match history, rating จากเพื่อน/โค้ช, หรือ integrate กับ UTR/WTN/ITF.
●	Scheduling: Calendar integration, invite & confirm, auto-reminder.
●	Court Integration: แสดง court ที่สนามคุณ + availability ทันที. โอกาส upsell (จองแพ็กเกจ, membership).
●	Community Features: Broadcast request, events/leagues ภายในสนาม, forum/กลุ่มย่อยตามระดับ.
●	Analytics สำหรับเจ้าของสนาม: เห็น usage pattern, popular time, retention ของผู้เล่น → ปรับ pricing/promotion.
●	Mobile-first: เพราะคนส่วนใหญ่หาคู่ทางมือถือ.
●	Edge cases: Option สำหรับ "just hitting" (ไม่แข่ง), beginner-friendly, accessibility (wheelchair tennis ถ้ามี), privacy control.


Phase 2 - Membership & Advanced Features
ระบบจองโค้ช (Coach Booking System)
ระบบ Member Tier / Privilege
ระบบ Member Pricing
ระบบรายงานกิจกรรมผู้ใช้

Phase 3 - Marketplace & Service Explanation

ระบบขายสินค้า/บริการในสนาม
ระบบ Voucher Redeem
Service Marketplace (Digital Service Layer)

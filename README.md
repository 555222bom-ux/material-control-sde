# Material Control SDE

แอปพลิเคชันระบบควบคุมและบริหารจัดการวัสดุอุปกรณ์โครงการ (Material Control SDE) ในรูปแบบของ Client-side Single Page Application (SPA) ที่ทำงานบนเว็บเบราว์เซอร์ได้ทันทีโดยไม่ต้องตั้งค่าเซิร์ฟเวอร์ยุ่งยาก

---

## คุณสมบัติเด่น (Key Features)

- **Dashboard:** สรุปภาพรวมยอดวัสดุคงเหลือ ความเคลื่อนไหว และแผนภูมิสรุปข้อมูลแยกตามหมวดหมู่
- **Master Data Management:** เพิ่ม แก้ไข จัดกลุ่ม ค้นหาข้อมูลวัสดุหลัก ข้อมูลหน่วย และผู้รับเหมาหลัก/รอง
- **Planning (PR) Management:** บันทึกแผนการสั่งซื้อตามใบ PR (Purchase Requisition)
- **Receiving System:** บันทึกรับพัสดุเข้าคลังจริง โดยสามารถดึงข้อมูลและอ้างอิงจากแผนใบ PR เพื่อป้องกันการรับเกินจำนวนค้างรับจริงได้
- **Request / Disbursing System:** ออกใบเบิกจ่ายวัสดุให้แก่ช่าง/ผู้รับเหมาในโครงการ พร้อมระบุรายละเอียดหน้างานและผู้ตรวจรับ
- **Offline-First Persistence:** จัดเก็บข้อมูลทั้งหมดในเครื่องผู้ใช้งานอย่างปลอดภัยผ่าน IndexedDB (`MaterialControlDB`)
- **Excel & PDF Export:** ส่งออกข้อมูลสรุปเป็นไฟล์ Excel (.xlsx) และใบเบิก/รายงานสรุปเป็น PDF (.pdf)

---

## โครงสร้างโครงการ (Project Structure)

```text
├── index.html                               # หน้าเว็บแอปพลิเคชันหลัก (GitHub Pages Ready)
├── MaterialControlSeed.js                   # ไฟล์เก็บ Seed Data สำรองในรูปแบบ JSON สำหรับนำเข้าเริ่มต้น
├── MaterialControlApp.html                  # ไฟล์แอปพลิเคชันสำรอง (เวอร์ชันเดิม)
├── import_new_project3_master_data.py      # สคริปต์ Python สำหรับแปลงข้อมูลวัสดุจาก SQLite ออกเป็น JSON/Excel
├── patch_category_name_migration.py        # สคริปต์ Python สำหรับอัปเดต Map รหัสหมวดหมู่จาก SQLite เข้าไปในหน้าเว็บ
├── Template/                                # โฟลเดอร์เก็บเทมเพลต Excel สำหรับจัดการข้อมูลนำเข้า/ส่งออก
└── New project 3/                           # โฟลเดอร์ฐานข้อมูล SQLite และสคริปต์ระบบแปลงข้อมูลภายใน
```

---

## วิธีการใช้งานแอปพลิเคชัน (How to Run)

1. **เปิดใช้งานหน้าเว็บ:** สามารถคลิกเปิดไฟล์ `index.html` บนเว็บเบราว์เซอร์ (Chrome, Edge, Firefox, Safari) เพื่อเริ่มต้นใช้งานได้ทันที
2. **การนำข้อมูลขึ้นโฮสต์บน GitHub:** หากอัปโหลดโค้ดชุดนี้ขึ้น GitHub สามารถเข้าไปเปิดใช้ฟีเจอร์ **GitHub Pages** ใน Setting ของ Repository เพื่อแปลงเป็นเว็บลิงก์ให้ทีมงานเปิดใช้งานร่วมกันได้ทันที

---

## วิธีการอัปเดตข้อมูลวัสดุจากฐานข้อมูล SQLite (Data Migration)

หากมีการแก้ไขฐานข้อมูล SQLite ในโฟลเดอร์ `New project 3` และต้องการนำมาอัปเดตลงในตัวเว็บ ให้ปฏิบัติดังนี้:

### 1. ติดตั้งไลบรารีที่จำเป็น
เปิด Terminal / Command Prompt แล้วพิมพ์คำสั่ง:
```bash
pip install openpyxl
```

### 2. รันสคริปต์ดึงข้อมูลวัสดุ (Master Data Import)
รันสคริปต์เพื่อสร้างไฟล์ JSON และ Excel รายการวัสดุใหม่:
```bash
python import_new_project3_master_data.py
```

### 3. รันสคริปต์อัปเดตหมวดหมู่วัสดุ (Category Mapping Patch)
รันสคริปต์เพื่ออัปเดต Mapping ของหมวดหมู่ลงในไฟล์หน้าเว็บ (`index.html` และ `MaterialControlApp.html`):
```bash
python patch_category_name_migration.py
```

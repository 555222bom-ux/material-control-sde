# Material Catalog

ระบบฐานข้อมูลวัสดุแบบ Desktop ใช้ Python Tkinter และ SQLite สำหรับค้นหา กรอง เพิ่มข้อมูล และ export รายการวัสดุ

## ไฟล์หลัก

- `material_catalog_app.py` - โปรแกรมหน้าจอฐานข้อมูลวัสดุ
- `เปิดโปรแกรมฐานข้อมูลวัสดุ.bat` - ไฟล์เปิดโปรแกรมบน Windows
- `build_materials_sqlite.py` - สร้างฐานข้อมูล SQLite จากไฟล์ Excel
- `build_materials_hierarchy_sqlite.py` - สร้างฐานข้อมูลแบบจัดลำดับ Type / Group / Sub-Group
- `build_wire_end_caps_summary.mjs` - สร้างสรุปรายการปลอกสี

## วิธีเปิดใช้งาน

ดับเบิลคลิกไฟล์ `เปิดโปรแกรมฐานข้อมูลวัสดุ.bat`

หรือรันด้วย Python:

```powershell
python material_catalog_app.py
```

## ข้อมูลที่ใช้

ฐานข้อมูลหลักอยู่ที่:

```text
outputs/db_split/materials_hierarchy.sqlite3
```

ไฟล์ผลลัพธ์และตัวอย่าง preview อยู่ในโฟลเดอร์ `outputs/`

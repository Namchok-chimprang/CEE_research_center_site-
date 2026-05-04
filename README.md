# Research Center Django Starter

โปรเจกต์นี้เป็นโครงตั้งต้นสำหรับเว็บไซต์ศูนย์วิจัย และเตรียมไว้สำหรับเชื่อม MCP ในอนาคต

## แอปที่มีตอนนี้

- `core`
- `researchers`
- `publications`
- `news`
- `contacts`

## เริ่มใช้งาน

```powershell
cd D:\2569\research_center_site
.\.venv\Scripts\Activate.ps1
python manage.py runserver
```

## ตั้งค่า `.env`

โปรเจกต์นี้อ่านค่าจากไฟล์ `.env` อัตโนมัติแล้ว

ไฟล์ที่ใช้คือ:

`D:\2569\research_center_site\.env`

ใส่ค่าแบบนี้:

```env
SCOPUS_API_KEY=your_scopus_api_key_here
DJANGO_DEBUG=True
```

หลังแก้ `.env` ให้หยุดแล้วเปิด `runserver` ใหม่หนึ่งครั้ง

## เข้าใช้งาน

- Website: `http://127.0.0.1:8000/`
- Admin: `http://127.0.0.1:8000/admin/`

## คำสั่งที่ควรใช้ต่อ

สร้าง superuser:

```powershell
python manage.py createsuperuser
```

เก็บ static files:

```powershell
python manage.py collectstatic
```

## สิ่งที่ควรทำต่อ

1. เปลี่ยนข้อความตัวอย่างให้เป็นข้อมูลจริงของศูนย์วิจัย
2. เพิ่มข้อมูลผ่าน Django admin
3. ปรับหน้าตาเว็บไซต์
4. สร้าง API สำหรับ Researchers, Publications, News
5. ค่อยเพิ่ม MCP server และ AI assistant

## Scopus sync

ถ้าต้องการดึง publication จาก Scopus:

```powershell
python manage.py sync_scopus --query "AU-ID(7004212771)" --count 10
```

หมายเหตุ:
- `count` ถูกจำกัดไว้ไม่เกิน `20`

ถ้าต้องการดึงจากชื่อ researcher โดยตรง:

```powershell
python manage.py sync_scopus --author-name "John Smith" --count 10
```

หรือชื่อแบบย่อ:

```powershell
python manage.py sync_scopus --author-name "J Smith" --count 10
```

ถ้าต้องการใช้รายชื่อจากหน้า Researchers ในเว็บ:

```powershell
python manage.py sync_scopus --from-site-researchers --count 10
```

ถ้าต้องการ sync นักวิจัยคนเดียวจาก `Researcher.id`:

```powershell
python manage.py sync_scopus --researcher-id 1 --count 10
```

หมายเหตุ:
- ถ้าใน `Researchers` มี `scopus_author_id` ระบบจะใช้ `AU-ID(...)` ให้ก่อน ซึ่งแม่นกว่า
- ถ้ายังไม่มี `scopus_author_id` ระบบจะ fallback ไปค้นจาก `full_name`
- ถ้า Scopus ไม่ส่ง author list ครบ ระบบจะพยายามเติม `all_authors` จาก OpenAlex และ Semantic Scholar ตามชื่อบทความ
- ปุ่ม sync จาก Django admin ใช้ `count=20` อัตโนมัติ

ถ้ามีไฟล์ CSV สำหรับ Impact Factor / JIF Quartile จากแหล่งภายนอก เช่น JCR:

```powershell
python manage.py sync_scopus --query "AU-ID(7004212771)" --count 10 --impact-factor-csv "D:\path\jcr_metrics.csv"
```

หมายเหตุ:
- Quartile ที่มาจาก Elsevier อาจอิง CiteScore percentile หรือ source metadata
- Impact Factor ไม่ได้มาจาก Scopus API โดยตรง จึงควรนำเข้าจากไฟล์ที่ได้รับอนุญาตจากแหล่งข้อมูลนั้น

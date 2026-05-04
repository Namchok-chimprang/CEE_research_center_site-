# Scopus API Test

ไฟล์ทดสอบอยู่ที่:

`scripts/scopus_api_test.py`

## วิธีใช้

1. เปิดไฟล์ `scopus_api_test.py`
2. เอา API key ของคุณไปแทนตรงนี้:

```python
API_KEY = "PASTE_YOUR_SCOPUS_API_KEY_HERE"
```

3. รันคำสั่ง:

```powershell
cd D:\2569\research_center_site
.\.venv\Scripts\python.exe scripts\scopus_api_test.py
```

## ถ้าสำเร็จ

คุณจะเห็นข้อความประมาณ:

```text
Scopus API call succeeded.
Results returned: 3
```

## ถ้าไม่สำเร็จ

สคริปต์จะพิมพ์ HTTP error หรือ network error ออกมาให้ดูตรง ๆ

## ข้อควรระวัง

- อย่า commit API key ลง git
- ถ้าจะใช้จริงใน Django โปรเจกต์ ควรย้าย key ไปไว้ใน `.env`

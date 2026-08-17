import re

with open('services/line_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

replacements = {
    '"选择区域 / Select Zone"':
    '"选择区域 (Select Zone / Pilih Zon / ဇုန်ရွေးပါ / জোন নির্বাচন করুন)"',
    
    'f"[{zone_name}] 请选择要完成的任务 (Select task):"':
    'f"[{zone_name}] 请选择要完成的任务 (Select task / Pilih tugas / တာဝန်ရွေးပါ / কাজ নির্বাচন করুন):"',
    
    'f"请选择【{item_name}】的使用数量 (Select quantity):"':
    'f"请选择【{item_name}】的使用数量 (Select quantity / Pilih kuantiti / အရေအတွက်ရွေးပါ / পরিমাণ নির্বাচন করুন):"',
    
    'f"请选择单位 (Select unit):"':
    'f"请选择单位 (Select unit / Pilih unit / ယူနစ်ရွေးပါ / ইউনিট নির্বাচন করুন):"',
    
    '"📸 请拍一张照片给我看 (Please take a photo):"':
    '"📸 请拍一张照片给我看 (Please take a photo / Sila ambil gambar / ဓာတ်ပုံရိုက်ပါ / একটি ছবি তুলুন):"'
}

for old, new in replacements.items():
    content = content.replace(old, new)

with open('services/line_service.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Patched line_service.py successfully.')

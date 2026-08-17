import os
import requests
import json
from PIL import Image, ImageDraw, ImageFont

# Load environment variables
from dotenv import load_dotenv
load_dotenv('.env')

ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
if not ACCESS_TOKEN:
    print("LINE_CHANNEL_ACCESS_TOKEN not found in .env")
    exit(1)

# 1. Generate Image (2500x1686)
print("Generating Rich Menu image...")
img = Image.new('RGB', (2500, 1686), color = (245, 242, 235))
d = ImageDraw.Draw(img)

# Try to find a font, fallback to default
try:
    font = ImageFont.truetype("arial.ttf", 60)
except:
    font = ImageFont.load_default()

# 6 regions: 2 rows, 3 cols
cols = 3
rows = 2
w = 2500 // cols
h = 1686 // rows

labels = [
    ["✅ 完成工作", "Done", "Selesai"],
    ["⚠️ 回报问题", "Problem", "Masalah"],
    ["📋 今日任务", "Tasks", "Tugas"],
    ["📦 用了资材", "Used Supply", "Pakai Bahan"],
    ["", "", ""],
    ["", "", ""]
]

for i in range(rows):
    for j in range(cols):
        idx = i * cols + j
        x1, y1 = j * w, i * h
        x2, y2 = (j + 1) * w, (i + 1) * h
        
        # Draw borders
        d.rectangle([x1, y1, x2, y2], outline=(200, 200, 200), width=5)
        
        # Draw text
        text_lines = labels[idx]
        text_y = y1 + h // 3
        for line in text_lines:
            if line:
                d.text((x1 + 50, text_y), line, fill=(45, 80, 22), font=font)
                text_y += 80

img.save('rich_menu.jpg')
print("Image saved as rich_menu.jpg")

# 2. Create Rich Menu
headers = {
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    'Content-Type': 'application/json'
}

data = {
    "size": {
        "width": 2500,
        "height": 1686
    },
    "selected": True,
    "name": "FarmWatch Worker Menu",
    "chatBarText": "Menu",
    "areas": [
        {
            "bounds": {"x": 0, "y": 0, "width": 833, "height": 843},
            "action": {"type": "message", "text": "✅ 完成工作"}
        },
        {
            "bounds": {"x": 833, "y": 0, "width": 833, "height": 843},
            "action": {"type": "message", "text": "⚠️ 回报问题"}
        },
        {
            "bounds": {"x": 1666, "y": 0, "width": 834, "height": 843},
            "action": {"type": "message", "text": "📋 今日任务"}
        },
        {
            "bounds": {"x": 0, "y": 843, "width": 833, "height": 843},
            "action": {"type": "message", "text": "📦 用了资材"}
        },
        {
            "bounds": {"x": 833, "y": 843, "width": 833, "height": 843},
            "action": {"type": "message", "text": "❓ 帮助"}
        },
        {
            "bounds": {"x": 1666, "y": 843, "width": 834, "height": 843},
            "action": {"type": "message", "text": "❓ 帮助"}
        }
    ]
}

print("Creating rich menu...")
res = requests.post('https://api.line.me/v2/bot/richmenu', headers=headers, json=data)
if res.status_code != 200:
    print(f"Error creating rich menu: {res.text}")
    exit(1)

rich_menu_id = res.json()['richMenuId']
print(f"Rich Menu created: {rich_menu_id}")

# 3. Upload Image
print("Uploading image...")
with open('rich_menu.jpg', 'rb') as f:
    img_headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'image/jpeg'
    }
    res = requests.post(f'https://api-data.line.me/v2/bot/richmenu/{rich_menu_id}/content', headers=img_headers, data=f)
    if res.status_code != 200:
        print(f"Error uploading image: {res.text}")
        exit(1)
print("Image uploaded.")

# 4. Set as default
print("Setting as default...")
res = requests.post(f'https://api.line.me/v2/bot/user/all/richmenu/{rich_menu_id}', headers=headers)
if res.status_code != 200:
    print(f"Error setting default: {res.text}")
    exit(1)

print("✅ Rich menu successfully deployed!")

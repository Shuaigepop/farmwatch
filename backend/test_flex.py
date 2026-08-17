import requests
import json
import os
from dotenv import load_dotenv

load_dotenv('.env')
token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
url = "https://api.line.me/v2/bot/message/push"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token}"
}

payload = {
    "to": "Udeadbeefdeadbeefdeadbeefdeadbeef",  # We expect a 400 with 'Failed to send messages' if the payload is valid but ID is wrong
    "messages": [
        {
            "type": "flex",
            "altText": "FarmWatch Menu",
            "contents": {
                "type": "bubble",
                "size": "mega",
                "header": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "FarmWatch 农场系统",
                            "weight": "bold",
                            "color": "#1DB446",
                            "size": "sm"
                        },
                        {
                            "type": "text",
                            "text": "👇 请选择功能 (Pilih / စာရင်း / নির্বাচন)",
                            "weight": "bold",
                            "size": "md",
                            "margin": "md",
                            "wrap": True
                        }
                    ]
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "md",
                    "contents": [
                        {
                            "type": "button",
                            "style": "primary",
                            "color": "#2D5016",
                            "action": {
                                "type": "message",
                                "label": "✅ 完成 Selesai সম্পন্ন ပြီး",
                                "text": "✅ 完成工作"
                            }
                        },
                        {
                            "type": "button",
                            "style": "secondary",
                            "action": {
                                "type": "message",
                                "label": "⚠️ 问题 Masalah সমস্যা ပြဿနာ",
                                "text": "⚠️ 回报问题"
                            }
                        },
                        {
                            "type": "button",
                            "style": "secondary",
                            "action": {
                                "type": "message",
                                "label": "📋 任务 Tugas কাজ တာဝန်",
                                "text": "📋 今日任务"
                            }
                        },
                        {
                            "type": "button",
                            "style": "secondary",
                            "action": {
                                "type": "message",
                                "label": "📦 资材 Bahan উপাদান ပစ္စည်း",
                                "text": "📦 用了资材"
                            }
                        }
                    ]
                }
            }
        }
    ]
}

res = requests.post(url, headers=headers, json=payload)
print(res.status_code)
print(res.text)

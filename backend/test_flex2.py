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
    "to": "Udeadbeefdeadbeefdeadbeefdeadbeef",
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
                        }
                    ]
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "md",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "margin": "md",
                            "spacing": "sm",
                            "cornerRadius": "md",
                            "borderWidth": "1px",
                            "borderColor": "#1DB446",
                            "paddingAll": "md",
                            "action": {
                                "type": "message",
                                "label": "Done",
                                "text": "✅ 完成工作"
                            },
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "✅ 完成工作 (Done)",
                                    "weight": "bold",
                                    "size": "md",
                                    "color": "#1DB446"
                                },
                                {
                                    "type": "text",
                                    "text": "🇲🇾 Selesai  🇧🇩 সম্পন্ন  🇲🇲 ပြီးပါပြီ",
                                    "size": "xs",
                                    "color": "#666666",
                                    "wrap": True
                                }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "margin": "md",
                            "spacing": "sm",
                            "cornerRadius": "md",
                            "borderWidth": "1px",
                            "borderColor": "#aaaaaa",
                            "paddingAll": "md",
                            "action": {
                                "type": "message",
                                "label": "Problem",
                                "text": "⚠️ 回报问题"
                            },
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "⚠️ 回报问题 (Problem)",
                                    "weight": "bold",
                                    "size": "md"
                                },
                                {
                                    "type": "text",
                                    "text": "🇲🇾 Masalah  🇧🇩 সমস্যা  🇲🇲 ပြဿနာ",
                                    "size": "xs",
                                    "color": "#666666",
                                    "wrap": True
                                }
                            ]
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

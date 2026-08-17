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
            "altText": "Menu",
            "contents": {
                "type": "bubble",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "action": {
                                "type": "postback",
                                "label": "Done",
                                "data": "action=done",
                                "inputOption": "openKeyboard",
                                "fillInText": "✅ 完成工作 "
                            },
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "Click me"
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

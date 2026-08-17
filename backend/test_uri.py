import requests
import json
import urllib.parse
import os
from dotenv import load_dotenv

load_dotenv('.env')
token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
url = "https://api.line.me/v2/bot/message/push"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token}"
}

text_to_fill = urllib.parse.quote("✅ 完成工作: ")
action_uri = f"https://line.me/R/msg/text/?{text_to_fill}"

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
                            "type": "button",
                            "action": {
                                "type": "uri",
                                "label": "Test",
                                "uri": action_uri
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

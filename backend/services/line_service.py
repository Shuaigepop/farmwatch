from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    MessagingApiBlob,
    ReplyMessageRequest,
    PushMessageRequest,
    TextMessage
)
import requests
from config import settings

class LineService:
    def __init__(self):
        self.configuration = Configuration(access_token=settings.LINE_CHANNEL_ACCESS_TOKEN)

    def send_text_message(self, group_id: str, text: str):
        # 發送文字訊息至群組 (Send text message to group)
        if not settings.LINE_CHANNEL_ACCESS_TOKEN:
            return
        with ApiClient(self.configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.push_message(
                PushMessageRequest(
                    to=group_id,
                    messages=[TextMessage(text=text)]
                )
            )

    def send_reply(self, reply_token: str, text: str):
        # 回覆訊息 (Reply to message)
        if not settings.LINE_CHANNEL_ACCESS_TOKEN:
            return
        with ApiClient(self.configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=[TextMessage(text=text)]
                )
            )

    def get_message_content(self, message_id: str) -> bytes:
        # 取得圖片或檔案內容 (Get image/file content)
        if not settings.LINE_CHANNEL_ACCESS_TOKEN:
            return b""
        with ApiClient(self.configuration) as api_client:
            line_bot_blob_api = MessagingApiBlob(api_client)
            message_content = line_bot_blob_api.get_message_content(message_id)
            return message_content

    def get_group_summary(self, group_id: str) -> dict:
        # 取得群組資訊 (Get group info)
        if not settings.LINE_CHANNEL_ACCESS_TOKEN:
            return {"groupName": "Unknown Group (No Token)"}
        try:
            with ApiClient(self.configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                summary = line_bot_api.get_group_summary(group_id)
                return {"groupName": summary.group_name}
        except Exception:
            return {"groupName": "Unknown Group"}

    def send_reply_flex_menu(self, reply_token: str):
        # 发送 Flex Message 互动选单 (Reply)
        if not settings.LINE_CHANNEL_ACCESS_TOKEN:
            return
            
        url = "https://api.line.me/v2/bot/message/reply"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.LINE_CHANNEL_ACCESS_TOKEN}"
        }
        
        payload = {
            "replyToken": reply_token,
            "messages": [
                {
                    "type": "flex",
                    "altText": "FarmWatch 互动选单 (Menu)",
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
                                    "text": "👇 互动选单 (Menu)",
                                    "weight": "bold",
                                    "size": "xl",
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
                                    "type": "box",
                                    "layout": "vertical",
                                    "margin": "md",
                                    "spacing": "sm",
                                    "cornerRadius": "md",
                                    "borderWidth": "2px",
                                    "borderColor": "#1DB446",
                                    "paddingAll": "md",
                                    "action": {
                                        "type": "postback",
                                        "label": "Done",
                                        "data": "action=done_init",
                                        "displayText": "✅ 完成工作"
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
                                            "text": "🇮🇩 Selesai  🇧🇩 সম্পন্ন  🇲🇲 ပြီးပါပြီ",
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
                                        "type": "postback",
                                        "label": "Problem",
                                        "data": "action=problem_init",
                                        "displayText": "⚠️ 回报问题"
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
                                            "text": "🇮🇩 Masalah  🇧🇩 সমস্যা  🇲🇲 ပြဿနာ",
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
                                        "type": "postback",
                                        "label": "Tasks",
                                        "data": "action=show_tasks",
                                        "displayText": "📋 今日任务"
                                    },
                                    "contents": [
                                        {
                                            "type": "text",
                                            "text": "📋 今日任务 (Tasks)",
                                            "weight": "bold",
                                            "size": "md"
                                        },
                                        {
                                            "type": "text",
                                            "text": "🇮🇩 Tugas  🇧🇩 কাজ  🇲🇲 တာဝန်",
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
                                        "type": "postback",
                                        "label": "Supply",
                                        "data": "action=supply_init",
                                        "displayText": "📦 用了资材"
                                    },
                                    "contents": [
                                        {
                                            "type": "text",
                                            "text": "📦 用了资材 (Supply)",
                                            "weight": "bold",
                                            "size": "md"
                                        },
                                        {
                                            "type": "text",
                                            "text": "🇮🇩 Bahan  🇧🇩 উপাদান  🇲🇲 ပစ္စည်း",
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
                                        "type": "postback",
                                        "label": "Delivery",
                                        "data": "action=delivery_init",
                                        "displayText": "🚚 回报出货"
                                    },
                                    "contents": [
                                        {
                                            "type": "text",
                                            "text": "🚚 回报出货 (Delivery)",
                                            "weight": "bold",
                                            "size": "md"
                                        },
                                        {
                                            "type": "text",
                                            "text": "🇮🇩 Pengiriman  🇧🇩 ডেলিভারি  🇲🇲 ပို့ဆောင်ခြင်း",
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
        
        try:
            requests.post(url, headers=headers, json=payload)
        except Exception as e:
            print(f"[LineService] Failed to send flex menu reply: {e}")
    def send_carousel_zones(self, reply_token: str, zones: list):
        if not settings.LINE_CHANNEL_ACCESS_TOKEN:
            return
        
        url = "https://api.line.me/v2/bot/message/reply"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.LINE_CHANNEL_ACCESS_TOKEN}"
        }
        
        bubbles = []
        for zone in zones[:10]:
            bubbles.append({
                "type": "bubble",
                "size": "micro",
                "header": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": zone.get('name', 'Zone'),
                            "weight": "bold",
                            "size": "lg",
                            "color": "#1DB446"
                        },
                        {
                            "type": "text",
                            "text": "选择区域 (Select Zone / Pilih Zon / ဇုန်ရွေးပါ / জোন নির্বাচন করুন)",
                            "size": "xxs",
                            "color": "#aaaaaa"
                        }
                    ]
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "paddingAll": "md",
                    "contents": [
                        {
                            "type": "button",
                            "style": "primary",
                            "color": "#2D5016",
                            "action": {
                                "type": "postback",
                                "label": "选择 (Select)",
                                "data": f"action=zone_selected&zone_id={zone.get('id')}"
                            }
                        }
                    ]
                }
            })
            
        payload = {
            "replyToken": reply_token,
            "messages": [
                {
                    "type": "flex",
                    "altText": "请选择区域 (Please select zone)",
                    "contents": {
                        "type": "carousel",
                        "contents": bubbles
                    }
                }
            ]
        }
        try:
            requests.post(url, headers=headers, json=payload)
        except Exception as e:
            print(f"Error sending carousel: {e}")

    def send_quick_reply_tasks(self, reply_token: str, tasks: list, zone_name: str):
        if not settings.LINE_CHANNEL_ACCESS_TOKEN:
            return
            
        items = []
        for task in tasks[:13]:
            items.append({
                "type": "action",
                "action": {
                    "type": "postback",
                    "label": task.get('title', 'Task')[:20],
                    "data": f"action=task_selected&task_id={task.get('id')}",
                    "displayText": f"✅ 完成 {task.get('title')}"
                }
            })
            
        url = "https://api.line.me/v2/bot/message/reply"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.LINE_CHANNEL_ACCESS_TOKEN}"
        }
        
        payload = {
            "replyToken": reply_token,
            "messages": [
                {
                    "type": "text",
                    "text": f"[{zone_name}] 请选择要完成的任务 (Select task / Pilih tugas / တာဝန်ရွေးပါ / কাজ নির্বাচন করুন):",
                    "quickReply": {
                        "items": items
                    }
                }
            ]
        }
        requests.post(url, headers=headers, json=payload)
        
    def send_carousel_inventory(self, reply_token: str, items: list):
        if not settings.LINE_CHANNEL_ACCESS_TOKEN:
            return
            
        url = "https://api.line.me/v2/bot/message/reply"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.LINE_CHANNEL_ACCESS_TOKEN}"
        }
        
        bubbles = []
        for item in items[:10]:
            bubbles.append({
                "type": "bubble",
                "size": "micro",
                "header": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": item.get('name', 'Item')[:15],
                            "weight": "bold",
                            "size": "lg",
                            "color": "#1DB446"
                        },
                        {
                            "type": "text",
                            "text": f"库存: {item.get('quantity', 0)} {item.get('unit', '')}",
                            "size": "xs",
                            "color": "#aaaaaa"
                        }
                    ]
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "paddingAll": "md",
                    "contents": [
                        {
                            "type": "button",
                            "style": "primary",
                            "color": "#2D5016",
                            "action": {
                                "type": "postback",
                                "label": "选择 (Select)",
                                "data": f"action=supply_selected&item_id={item.get('id')}"
                            }
                        }
                    ]
                }
            })
            
        payload = {
            "replyToken": reply_token,
            "messages": [
                {
                    "type": "flex",
                    "altText": "请选择资材 (Select supply)",
                    "contents": {
                        "type": "carousel",
                        "contents": bubbles
                    }
                }
            ]
        }
        requests.post(url, headers=headers, json=payload)

    def send_quick_reply_quantities(self, reply_token: str, item_name: str, item_id: int):
        if not settings.LINE_CHANNEL_ACCESS_TOKEN:
            return
            
        items = []
        for q in [1, 2, 3, 4, 5, 10]:
            items.append({
                "type": "action",
                "action": {
                    "type": "postback",
                    "label": str(q),
                    "data": f"action=qty_selected&item_id={item_id}&qty={q}",
                    "displayText": str(q)
                }
            })
            
        # Add "More..." option opening keyboard
        items.append({
            "type": "action",
            "action": {
                "type": "postback",
                "label": "更多 (More)",
                "data": f"action=qty_selected_custom&item_id={item_id}",
                "inputOption": "openKeyboard",
                "fillInText": f"数量: "
            }
        })
            
        url = "https://api.line.me/v2/bot/message/reply"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.LINE_CHANNEL_ACCESS_TOKEN}"
        }
        
        payload = {
            "replyToken": reply_token,
            "messages": [
                {
                    "type": "text",
                    "text": f"请选择【{item_name}】的使用数量 (Select quantity / Pilih kuantiti / အရေအတွက်ရွေးပါ / পরিমাণ নির্বাচন করুন):",
                    "quickReply": {
                        "items": items
                    }
                }
            ]
        }
        requests.post(url, headers=headers, json=payload)

    def send_quick_reply_units(self, reply_token: str, item_name: str, item_id: int, qty: int, unit: str):
        if not settings.LINE_CHANNEL_ACCESS_TOKEN:
            return
            
        items = []
        units_list = [unit] if unit else ["包 (Bag)", "盒 (Box)", "瓶 (Bottle)", "桶 (Bucket)", "公斤 (KG)"]
        for u in units_list:
            items.append({
                "type": "action",
                "action": {
                    "type": "postback",
                    "label": u[:20],
                    "data": f"action=unit_selected&item_id={item_id}&qty={qty}&unit={u}",
                    "displayText": f"{qty} {u}"
                }
            })
            
        url = "https://api.line.me/v2/bot/message/reply"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.LINE_CHANNEL_ACCESS_TOKEN}"
        }
        
        payload = {
            "replyToken": reply_token,
            "messages": [
                {
                    "type": "text",
                    "text": f"请选择单位 (Select unit / Pilih unit / ယူနစ်ရွေးပါ / ইউনিট নির্বাচন করুন):",
                    "quickReply": {
                        "items": items
                    }
                }
            ]
        }
        requests.post(url, headers=headers, json=payload)
        
    def send_camera_quick_reply(self, reply_token: str):
        if not settings.LINE_CHANNEL_ACCESS_TOKEN:
            return
            
        url = "https://api.line.me/v2/bot/message/reply"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.LINE_CHANNEL_ACCESS_TOKEN}"
        }
        
        payload = {
            "replyToken": reply_token,
            "messages": [
                {
                    "type": "text",
                    "text": "📸 请拍一张照片给我看 (Please take a photo / Sila ambil gambar / ဓာတ်ပုံရိုက်ပါ / একটি ছবি তুলুন):",
                    "quickReply": {
                        "items": [
                            {
                                "type": "action",
                                "action": {
                                    "type": "camera",
                                    "label": "📸 拍照 (Camera)"
                                }
                            },
                            {
                                "type": "action",
                                "action": {
                                    "type": "cameraRoll",
                                    "label": "🖼️ 相簿 (Gallery)"
                                }
                            }
                        ]
                    }
                }
            ]
        }
        requests.post(url, headers=headers, json=payload)

line_service = LineService()

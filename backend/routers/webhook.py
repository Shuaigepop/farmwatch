from fastapi import APIRouter, Request, HTTPException, Depends, BackgroundTasks
from linebot.v3.webhook import WebhookParser
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent, ImageMessageContent, JoinEvent, PostbackEvent
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from config import settings
from models.models import LineGroup, Message, Photo
from services.line_service import line_service
from services.storage_service import storage_service
from services.ai_service import ai_service
from deps import get_db
from database import AsyncSessionLocal
import json
from datetime import datetime, timezone
import re

router = APIRouter(prefix="/api/webhook", tags=["webhook"])
parser = WebhookParser(settings.LINE_CHANNEL_SECRET)

# Simple in-memory state tracking for LINE bot interactions
# Key: target_id (group_id or user_id), Value: dict of state
_bot_states = {}

async def process_image_analysis(photo_id: int, target_id: str, file_path: str):
    try:
        import os
        # file_path is just a filename, construct full path
        full_path = os.path.join(settings.UPLOAD_DIR, file_path)
        print(f"[AI] Starting analysis for photo {photo_id}, path: {full_path}")
        
        analysis_text = await ai_service.analyze_image(full_path)
        print("[AI] Analysis result received.")
        # Parse JSON
        analysis_data = json.loads(analysis_text)
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Photo).where(Photo.id == photo_id))
            photo = result.scalar_one_or_none()
            if photo:
                photo.ai_analysis = analysis_text
                photo.health_status = analysis_data.get("status", "pending")
                photo.analyzed_at = datetime.now(timezone.utc)
                
                # Check for planting verification
                is_valid = analysis_data.get("is_valid_farm_photo", True)
                is_planting = analysis_data.get("is_planting_verification", False)
                planting_status = analysis_data.get("planting_status", None)
                
                if not is_valid:
                    photo.health_status = "rejected"
                    reply_msg = "\u26a0\ufe0f [Invalid Photo]\nAI determined this is not a farm-related photo.\nPlease take a clear photo of the farm/crops."
                else:
                    reply_msg = "\U0001f4f8 AI Analysis Complete\nStatus: " + str(photo.health_status) + "\nNotes: " + str(analysis_data.get('notes', ''))
                    
                    # Check if this is a foreman verification photo
                    is_verification = analysis_data.get("is_task_verification", False)
                    verified_zone_id = analysis_data.get("verified_zone_id", None)
                    
                    if is_verification and photo.farm_id:
                        from models.models import Task
                        pending_q = select(Task).where(
                            Task.farm_id == photo.farm_id,
                            Task.status.in_(["pending", "in_progress"]),
                            Task.target_role == "worker"
                        )
                        if verified_zone_id:
                            pending_q = pending_q.where(Task.zone_id == verified_zone_id)
                        pending_res = await session.execute(pending_q)
                        pending_tasks = pending_res.scalars().all()
                        
                        if pending_tasks:
                            completed_names = []
                            for pt in pending_tasks:
                                pt.status = "completed"
                                pt.completed_at = datetime.now(timezone.utc)
                                completed_names.append(pt.title)
                            reply_msg += "\n\n\u2705 [Foreman Verified] " + str(len(completed_names)) + " tasks marked complete:\n" + "\n".join(completed_names)
                    
                    if is_planting:
                        from models.models import HarvestPlan
                        pending_plans_res = await session.execute(select(HarvestPlan).where(
                            HarvestPlan.farm_id == photo.farm_id,
                            HarvestPlan.status == "pending_verification"
                        ))
                        pending_plans = pending_plans_res.scalars().all()
                        
                        if pending_plans:
                            if planting_status == "approved":
                                for plan in pending_plans:
                                    plan.status = "growing"
                                reply_msg += "\n\n✅ [种植确认] AI 已确认种植照片！采收倒数正式启动。 (Planting verified! Countdown started.)"
                            elif planting_status == "flagged":
                                reply_msg += "\n\n⚠️ [工头确认需求] 照片无法自动确认为合格种植，已通知工头查验。 (Foreman review required for planting.)"
                
                await session.commit()
                print(f"[AI] Photo {photo_id} updated: status={photo.health_status}")
                
        # Use Push Message instead of Reply Message to avoid timeout
        if target_id:
            line_service.send_text_message(target_id, reply_msg)
    except Exception as e:
        import traceback
        print(f"[AI ERROR] process_image_analysis failed: {e}")
        traceback.print_exc()

async def process_text_intent(text: str, farm_id: int, target_id: str):
    if not farm_id or not target_id:
        return
    try:
        print(f"[AI] Parsing intent for: {text}")
        intent_json = await ai_service.parse_bot_intent(text)
        print("[AI] Intent result received.")
        data = json.loads(intent_json)
        
        if data.get("intent") in ["inventory_consume", "inventory_add"]:
            item_name = data.get("item_name")
            qty = data.get("quantity")
            if not item_name or qty is None:
                line_service.send_text_message(target_id, "🤖 我似乎不明白你要操作哪個物品或數量。")
                return
                
            qty = float(qty)
            is_consume = data["intent"] == "inventory_consume"
            
            async with AsyncSessionLocal() as session:
                # Find the item
                from models.models import InventoryItem
                result = await session.execute(
                    select(InventoryItem)
                    .where(InventoryItem.farm_id == farm_id)
                    .where(InventoryItem.name.like(f"%{item_name}%"))
                )
                item = result.scalars().first()
                
                if item:
                    old_qty = item.quantity
                    if is_consume:
                        item.quantity = max(0, item.quantity - qty)
                        reply = f"✅ 已記錄消耗：{item_name} -{qty} {item.unit} (剩餘 {item.quantity} {item.unit})"
                    else:
                        item.quantity += qty
                        reply = f"✅ 已記錄新增：{item_name} +{qty} {item.unit} (目前 {item.quantity} {item.unit})"
                    await session.commit()
                else:
                    if is_consume:
                        reply = f"⚠️ 找不到名為「{item_name}」的庫存項目，無法扣減。"
                    else:
                        # Auto create
                        new_item = InventoryItem(
                            farm_id=farm_id,
                            item_type="other",
                            name=item_name,
                            quantity=qty,
                            unit=data.get("unit", "個")
                        )
                        session.add(new_item)
                        await session.commit()
                        reply = f"✨ 已建立新庫存：{item_name}，數量 {qty} {data.get('unit', '個')}"
                        
            line_service.send_text_message(target_id, reply)
        else:
            line_service.send_text_message(target_id, "\U0001f916 [System] This farm requires PHOTO proof for work reports!\nPlease send a photo to record progress. Text chat will not be recorded.\n\n\U0001f916 [\u7cfb\u7edf] \u519c\u573a\u4e0d\u63a5\u53d7\u7eaf\u6587\u5b57\u5de5\u4f5c\u6c47\u62a5\uff01\u8bf7\u62cd\u7167\u4e0a\u4f20\u8bb0\u5f55\u5de5\u4f5c\u8fdb\u5ea6\u3002")

    except Exception as e:
        print(f"[AI ERROR] process_text_intent failed: {e}")

async def handle_rich_menu_intent(text: str, farm_id: int, target_id: str, reply_token: str = None):
    """Handle Rich Menu clicks or stateful replies"""
    text = text.strip()
    
    # 1. Check if user is in a state answering a prompt
    state = _bot_states.get(target_id)
    if state:
        if state["action"] == "complete_task":
            # Expecting a number
            if text.isdigit():
                idx = int(text) - 1
                tasks = state.get("tasks", [])
                if 0 <= idx < len(tasks):
                    task_id = tasks[idx]["id"]
                    task_title = tasks[idx]["title"]
                    zone_name = tasks[idx]["zone_name"]
                    
                    async with AsyncSessionLocal() as session:
                        from models.models import Task
                        res = await session.execute(select(Task).where(Task.id == task_id))
                        t = res.scalar_one_or_none()
                        if t:
                            t.status = "completed"
                            t.completed_at = datetime.now(timezone.utc)
                            await session.commit()
                            reply = f"✅ 已完成 (Done / Selesai / ပြီးပြီ / সম্পন্ন)! \n{zone_name} - {task_title}"
                            if reply_token:
                                line_service.send_reply(reply_token, reply)
                            else:
                                line_service.send_text_message(target_id, reply)
                    
                    # Clear state
                    del _bot_states[target_id]
                    return True
                else:
                    if reply_token:
                        line_service.send_reply(reply_token, "⚠️ 无效的号码 (Invalid number / Nombor tidak sah / ဂဏန်းမမှန်ပါ / အကျုံးမဝင်သောနံပါတ်)")
                    else:
                        line_service.send_text_message(target_id, "⚠️ 无效的号码 (Invalid number / Nombor tidak sah / ဂဏန်းမမှန်ပါ / အကျုံးမဝင်သောနံပါတ်)")
                    return True
            else:
                # If they say something else, cancel the state
                del _bot_states[target_id]
                
        elif state["action"] == "report_problem":
            # Expecting photo, but got text. We will translate it.
            if not text.startswith("✅") and not text.startswith("📸") and not text.startswith("⚠️"):
                try:
                    translated = await ai_service.translate_to_chinese(text)
                    reply = f"✅ 已收到您的备注 (Notes received)!\n\n[AI 翻译 / AI Translate]:\n{translated}"
                except Exception as e:
                    reply = "✅ 已收到您的备注 (Notes received)!"
                
                if reply_token:
                    line_service.send_reply(reply_token, reply)
                else:
                    line_service.send_text_message(target_id, reply)
                del _bot_states[target_id]
                return True
            # We expect a photo, but got text.
            if "出货" not in text:
                 del _bot_states[target_id]
        elif state["action"] == "report_harvest_photo":
             # We expect a photo, but got text.
             if "出货" not in text:
                 del _bot_states[target_id]
        elif state["action"] == "report_harvest_data":
            # Parse text like "570kg 出9回0" or "570 9 0"
            import re
            nums = re.findall(r'\d+(?:\.\d+)?', text)
            if len(nums) == 3:
                weight = float(nums[0])
                baskets_out = int(float(nums[1]))
                baskets_in = int(float(nums[2]))
                photo_id = state.get("photo_id")
                
                async with AsyncSessionLocal() as session:
                    from models.models import DeliveryRecord, InventoryItem, User
                    user = await session.execute(select(User).where(User.farm_id == farm_id))
                    user = user.scalars().first() # just fallback uploader if none
                    
                    record = DeliveryRecord(
                        farm_id=farm_id,
                        photo_id=photo_id,
                        total_weight_kg=weight,
                        baskets_out=baskets_out,
                        baskets_in=baskets_in,
                        uploader_id=user.id if user else None
                    )
                    session.add(record)
                    
                    # Update inventory
                    inv_res = await session.execute(select(InventoryItem).where(
                        InventoryItem.farm_id == farm_id,
                        InventoryItem.name.like("%Kosong%") # Hardcoded for now
                    ))
                    basket_item = inv_res.scalars().first()
                    if basket_item:
                        basket_item.quantity = max(0, basket_item.quantity - baskets_out + baskets_in)
                    
                    await session.commit()
                
                reply = f"✅ 已成功纪录出货！(Delivery recorded)\n📦 重量(Weight): {weight}kg\n🧺 借出篮子(Baskets Out): {baskets_out}\n🧺 收回篮子(Baskets In): {baskets_in}"
                if reply_token:
                    line_service.send_reply(reply_token, reply)
                else:
                    line_service.send_text_message(target_id, reply)
                del _bot_states[target_id]
                return True
            else:
                # STRICT Warning: Re-prompt for exactly 3 numbers
                error_reply = (
                    "⚠️ 格式错误！请务必依照格式输入三个数字，中间用空格隔开。\n"
                    "⚠️ Format error! You must enter exactly three numbers separated by spaces.\n"
                    "⚠️ Format salah! Mesti masukkan tepat tiga nombor diasingkan dengan ruang.\n"
                    "⚠️ ပုံစံမှားနေပါသည်! (Weight) (Out) (In) အတိုင်း ဂဏန်း ၃ လုံး ရိုက်ပါ။\n"
                    "⚠️ ფორმატის შეცდომა! (This is an example)\n"
                    "(例如 / e.g. / cth / ဥပမာ : 570 9 0)"
                )
                if reply_token:
                    line_service.send_reply(reply_token, error_reply)
                else:
                    line_service.send_text_message(target_id, error_reply)
                # DO NOT delete state, wait for them to retry
                return True
        elif state["action"] == "inventory":
            # Expecting number and quantity
            parts = text.split()
            if len(parts) >= 2 and parts[0].isdigit():
                idx = int(parts[0]) - 1
                items = state.get("items", [])
                if 0 <= idx < len(items):
                    try:
                        qty = float(parts[1])
                        item_id = items[idx]["id"]
                        item_name = items[idx]["name"]
                        unit = items[idx]["unit"]
                        
                        async with AsyncSessionLocal() as session:
                            from models.models import InventoryItem
                            res = await session.execute(select(InventoryItem).where(InventoryItem.id == item_id))
                            inv = res.scalar_one_or_none()
                            if inv:
                                inv.quantity = max(0, inv.quantity - qty)
                                await session.commit()
                                reply = f"✅ 已記錄 (Recorded / Direkodkan / မှတ်တမ်းတင်ထားသည် / রেকর্ড করা হয়েছে): \n{item_name} -{qty} {unit}"
                                if reply_token:
                                    line_service.send_reply(reply_token, reply)
                                else:
                                    line_service.send_text_message(target_id, reply)
                        del _bot_states[target_id]
                        return True
                    except ValueError:
                        pass
            del _bot_states[target_id]

    # 2. Check if text matches Rich Menu buttons
    # "✅ 完成工作" or "Done" or "Selesai"
    if "✅" in text or text.lower() in ["done", "selesai", "সম্পন্ন", "ပြီးပြီ"]:
        async with AsyncSessionLocal() as session:
            from models.models import Task, FarmZone
            from sqlalchemy.orm import selectinload
            query = select(Task).options(selectinload(Task.zone)).where(
                Task.farm_id == farm_id, 
                Task.status != "completed"
            ).order_by(Task.due_date.asc())
            result = await session.execute(query)
            tasks = result.scalars().all()
            
            if not tasks:
                line_service.send_text_message(target_id, "✅ 目前沒有待辦任務 (No pending tasks / Tiada tugas yang belum selesai / လုပ်ဆောင်ရန်မရှိပါ / কোন কাজ বাকি নেই)")
                return True
                
            reply_lines = ["📋 待完成任務 / Pending Tasks:\n"]
            state_tasks = []
            for i, t in enumerate(tasks):
                zone_name = t.zone.name if t.zone else "Global"
                reply_lines.append(f"{i+1}️⃣ [{zone_name}] {t.title}")
                state_tasks.append({"id": t.id, "title": t.title, "zone_name": zone_name})
                
            reply_lines.append("\n▶️ 回复号码以完成任务 / Reply number:")
            _bot_states[target_id] = {"action": "complete_task", "tasks": state_tasks}
            if reply_token:
                line_service.send_reply(reply_token, "\n".join(reply_lines))
            else:
                line_service.send_text_message(target_id, "\n".join(reply_lines))
        return True

    # "⚠️ 回报问题" or "Problem" or "Masalah"
    if "⚠️" in text or text.lower() in ["problem", "masalah", "সমস্যা", "ပြဿနာ"] or "回报问题" in text or "回报" in text:
        reply = "请拍一张照片给我们看 📷\nPlease send a photo 📷\nTolong kirim foto 📷"
        _bot_states[target_id] = {"action": "report_problem"}
        if reply_token:
            line_service.send_reply(reply_token, reply)
        else:
            line_service.send_text_message(target_id, reply)
        return True

    # "🚚 回报出货" or "Delivery" or "Harvest"
    if "🚚" in text or "出货" in text or "harvest" in text.lower() or "delivery" in text.lower():
        reply = "照片收到前，请先上传出货单/收据的照片 📷\nPlease upload a photo of the delivery receipt 📷\nSila muat naik gambar resit penghantaran 📷\nပို့ဆောင်မှု ပြေစာ ဓာတ်ပုံကို တင်ပေးပါ 📷\nঅনুগ্রহ করে ডেলিভারি রসিদের একটি ছবি আপলোড করুন 📷"
        _bot_states[target_id] = {"action": "report_harvest_photo"}
        if reply_token:
            line_service.send_reply(reply_token, reply)
        else:
            line_service.send_text_message(target_id, reply)
        return True

    # "📦 用了资材" or "Used Supply" or "Pakai Bahan"
    if "📦" in text or "used" in text.lower() or "pakai" in text.lower() or "资材" in text:
        async with AsyncSessionLocal() as session:
            from models.models import InventoryItem
            result = await session.execute(select(InventoryItem).where(InventoryItem.farm_id == farm_id))
            items = result.scalars().all()
            
            if not items:
                if reply_token:
                    line_service.send_reply(reply_token, f"📦 仓库为空 (Inventory empty / Stok kosong / ကုန်ပစ္စည်းမရှိပါ / স্টক খালি) - Debug: FarmID={farm_id}")
                else:
                    line_service.send_text_message(target_id, f"📦 仓库为空 (Inventory empty / Stok kosong / ကုန်ပစ္စည်းမရှိပါ / স্টক খালি) - Debug: FarmID={farm_id}")
                return True
                
            reply_lines = ["📦 庫存清單 / Inventory:\n"]
            state_items = []
            for i, it in enumerate(items):
                reply_lines.append(f"{i+1}️⃣ {it.name} ({it.quantity} {it.unit})")
                state_items.append({"id": it.id, "name": it.name, "unit": it.unit})
                
            reply_lines.append("\n▶️ 回复「号码 数量」:\n例如 / Example: 1 5")
            _bot_states[target_id] = {"action": "inventory", "items": state_items}
            if reply_token:
                line_service.send_reply(reply_token, "\n".join(reply_lines))
            else:
                line_service.send_text_message(target_id, "\n".join(reply_lines))
        return True

    # "📋 今日任务" or "Today Tasks"
    if "📋" in text or "tasks" in text.lower() or "tugas" in text.lower() or "今日任务" in text or "任务" in text:
        async with AsyncSessionLocal() as session:
            from models.models import Task
            from sqlalchemy.orm import selectinload
            query = select(Task).options(selectinload(Task.zone)).where(
                Task.farm_id == farm_id, 
                Task.status != "completed"
            ).order_by(Task.due_date.asc())
            result = await session.execute(query)
            tasks = result.scalars().all()
            
            if not tasks:
                if reply_token:
                    line_service.send_reply(reply_token, "✅ 今天无任务 (No tasks today)")
                else:
                    line_service.send_text_message(target_id, "✅ 今天无任务 (No tasks today)")
                return True
                
            reply_lines = ["📋 今日任務 / Today Tasks:\n"]
            for i, t in enumerate(tasks):
                zone_name = t.zone.name if t.zone else "Global"
                reply_lines.append(f"• [{zone_name}] {t.title}")
            
            if reply_token:
                line_service.send_reply(reply_token, "\n".join(reply_lines))
            else:
                line_service.send_text_message(target_id, "\n".join(reply_lines))
        return True

    # Check for Flex Menu triggers ("?", "menu", "选单", "菜单")
    if text.lower() in ["?", "menu", "menue", "选单", "菜单", "選單", "菜單"]:
        if reply_token:
            line_service.send_reply_flex_menu(reply_token)
        else:
            line_service.send_flex_menu(target_id)  # Fallback if I later implement push again
        return True

    return False

@router.post("/line")
async def line_webhook(request: Request, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    signature = request.headers.get("X-Line-Signature", "")
    body = await request.body()
    body_text = body.decode('utf-8')

    try:
        events = parser.parse(body_text, signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    for event in events:
        if isinstance(event, JoinEvent):
            # 機器人加入群組 (Bot joined group)
            source = event.source
            if source.type == "group":
                group_id = source.group_id
                
                # Check if exists
                res = await db.execute(select(LineGroup).where(LineGroup.line_group_id == group_id))
                if not res.scalar_one_or_none():
                    group_info = line_service.get_group_summary(group_id)
                    group_name = group_info.get("groupName")
                    
                    # Try to auto-link farm by name
                    from models.models import Farm
                    res_farm = await db.execute(select(Farm).where(Farm.name == group_name))
                    farm = res_farm.scalar_one_or_none()
                    farm_id = farm.id if farm else None
                    
                    new_group = LineGroup(
                        line_group_id=group_id,
                        group_name=group_name,
                        farm_id=farm_id
                    )
                    db.add(new_group)
                    await db.commit()
                    
                    if farm_id:
                        line_service.send_reply(event.reply_token, f"FarmWatch機器人已加入！成功自動綁定至农场「{group_name}」。")
                    else:
                        line_service.send_reply(event.reply_token, f"FarmWatch機器人已加入！无法找到匹配的农场名称 ({group_name})，请在系统中手动绑定。")

        elif isinstance(event, MessageEvent):
            source = event.source
            group_id = None
            target_id = source.user_id
            if source.type == "group":
                group_id = source.group_id
                target_id = group_id
                
            # Find farm_id if it's from a group
            farm_id = None
            if group_id:
                res = await db.execute(select(LineGroup).where(LineGroup.line_group_id == group_id))
                group = res.scalar_one_or_none()
                if group:
                    if group.farm_id:
                        farm_id = group.farm_id
                    else:
                        # Fetch latest name in case they renamed the LINE group
                        group_info = line_service.get_group_summary(group_id)
                        latest_name = group_info.get("groupName")
                        if latest_name:
                            group.group_name = latest_name
                            
                            from models.models import Farm
                            res_farm = await db.execute(select(Farm).where(Farm.name == latest_name))
                            farm = res_farm.scalar_one_or_none()
                            if farm:
                                group.farm_id = farm.id
                                farm_id = farm.id
                        await db.commit()
                else:
                    # Dynamic link fallback
                    group_info = line_service.get_group_summary(group_id)
                    group_name = group_info.get("groupName")
                    if group_name:
                        from models.models import Farm
                        res_farm = await db.execute(select(Farm).where(Farm.name == group_name))
                        farm = res_farm.scalar_one_or_none()
                        farm_id = farm.id if farm else None
                        
                        new_group = LineGroup(
                            line_group_id=group_id,
                            group_name=group_name,
                            farm_id=farm_id
                        )
                        db.add(new_group)
                        await db.commit()

            if isinstance(event.message, TextMessageContent):
                # 處理文字訊息 (Handle text message)
                text = event.message.text
                new_msg = Message(
                    line_user_id=source.user_id,
                    line_group_id=group_id,
                    farm_id=farm_id,
                    content=text,
                    message_type="text"
                )
                db.add(new_msg)
                await db.commit()
                
                if text.strip() in ["@menu", "@菜单", "主选单", "选单"]:
                    if getattr(event, 'reply_token', None):
                        line_service.send_reply_flex_menu(event.reply_token)
                    return True
                
                if "回报出货" in text or "harvest" in text.lower() or "delivery" in text.lower():
                    reply = "照片收到前，请先上传出货单/收据的照片 📷\nPlease upload a photo of the delivery receipt 📷\nSila muat naik gambar resit penghantaran 📷"
                    _bot_states[target_id] = {"action": "report_harvest_photo"}
                    if getattr(event, 'reply_token', None):
                        line_service.send_reply(event.reply_token, reply)
                    else:
                        line_service.send_text_message(target_id, reply)
                    return True

                if text.startswith("@farms"):
                    res = await db.execute(select(Farm))
                    farms = res.scalars().all()
                    reply = "Available Farms:\n" + "\n".join([f"ID: {f.id} - {f.name}" for f in farms])
                    if reply_token:
                        line_service.send_reply(reply_token, reply)
                    else:
                        line_service.send_text_message(target_id, reply)
                    return True

                if text.startswith("@link "):
                    try:
                        target_farm = int(text.split(" ")[1].strip())
                        if group_id:
                            res = await db.execute(select(LineGroup).where(LineGroup.line_group_id == group_id))
                            grp = res.scalar_one_or_none()
                            if grp:
                                grp.farm_id = target_farm
                                await db.commit()
                                reply = f"✅ 已强制连结到农场 ID: {target_farm}"
                                if reply_token:
                                    line_service.send_reply(reply_token, reply)
                                else:
                                    line_service.send_text_message(target_id, reply)
                        return True
                    except:
                        pass

                if text.startswith("@test"):
                    reply = "🧪 老板专属测试按钮 (Boss Test Menu):"
                    quick_reply = {
                        "items": [
                            {"type": "action", "action": {"type": "postback", "label": "测试 11AM 浇水", "data": "action=test_11am", "displayText": "测试 11AM 浇水"}},
                            {"type": "action", "action": {"type": "postback", "label": "测试 6PM 查账", "data": "action=test_6pm", "displayText": "测试 6PM 查账"}},
                            {"type": "action", "action": {"type": "postback", "label": "测试 7PM 总结", "data": "action=test_7pm", "displayText": "测试 7PM 总结"}},
                            {"type": "action", "action": {"type": "postback", "label": "测试 周一拍照", "data": "action=test_monday", "displayText": "测试 周一拍照"}}
                        ]
                    }
                    if not settings.LINE_CHANNEL_ACCESS_TOKEN:
                        return True
                    import requests
                    url = "https://api.line.me/v2/bot/message/reply"
                    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {settings.LINE_CHANNEL_ACCESS_TOKEN}"}
                    payload = {"replyToken": event.reply_token, "messages": [{"type": "text", "text": reply, "quickReply": quick_reply}]}
                    requests.post(url, headers=headers, json=payload, timeout=5)
                    return True

            # Check for rich menu intents first
                handled = await handle_rich_menu_intent(text, farm_id, target_id, event.reply_token)
                
                if not handled and text.strip().lower().startswith("@bot"):
                    # Remove @bot prefix
                    command_text = text.strip()[4:].strip()
                    if command_text:
                        background_tasks.add_task(process_text_intent, command_text, farm_id, target_id)
                        
            elif isinstance(event.message, ImageMessageContent):
                # 處理圖片訊息 (Handle image message)
                image_content = line_service.get_message_content(event.message.id)
                filename = await storage_service.save_image(image_content, f"{event.message.id}.jpg")
                thumbnail = await storage_service.create_thumbnail(filename)
                
                new_msg = Message(
                    line_user_id=source.user_id,
                    line_group_id=group_id,
                    farm_id=farm_id,
                    message_type="image"
                )
                db.add(new_msg)
                await db.flush() # get new_msg.id
                
                new_photo = Photo(
                    message_id=new_msg.id,
                    farm_id=farm_id,
                    file_path=filename,
                    thumbnail_path=thumbnail
                )
                
                # Check if expecting a problem photo
                state = _bot_states.get(target_id)
                skip_analysis = False
                if state and state.get("action") == "report_problem":
                    new_photo.health_status = "warning" # pre-mark as warning
                    del _bot_states[target_id]
                    reply = "📸 照片已收到！AI正在帮您辨识与分析中，请稍候... (Photo received, AI is analyzing... / Sedang dianalisis...)"
                    line_service.send_text_message(target_id, reply)
                elif state and state.get("action") == "report_harvest_photo":
                    new_photo.health_status = "receipt" # tag as receipt
                    skip_analysis = True
                    _bot_states[target_id] = {"action": "report_harvest_data", "photo_id": new_photo.id}
                    reply = "✅ 照片已收到！请回复出货重量及篮子借出/收回数量 (例如: 570kg 出9回0)\n✅ Photo received! Reply with weight and baskets out/in (e.g., 570kg 9 0)\n✅ Gambar diterima! Sila balas berat dan bakul keluar/masuk (cth: 570kg 9 0)\n✅ ဓာတ်ပုံရရှိပါပြီ။ အလေးချိန်နှင့် တောင်းထွက်/ဝင် ကို စာပြန်ပေးပါ (ဥပမာ- 570kg 9 0)\n✅ ছবি পাওয়া গেছে! ওজন এবং ঝুড়ি দেওয়া/নেওয়ার পরিমাণ লিখে পাঠান (যেমন: 570kg 9 0)"
                    line_service.send_text_message(target_id, reply)
                
                db.add(new_photo)
                await db.commit()
                await db.refresh(new_photo)
                
                # trigger background analysis
                if not skip_analysis:
                    background_tasks.add_task(process_image_analysis, new_photo.id, target_id, new_photo.file_path)

        elif isinstance(event, PostbackEvent):
            source = event.source
            group_id = None
            target_id = source.user_id
            if source.type == "group":
                group_id = source.group_id
                target_id = group_id
                
            farm_id = None
            if group_id:
                res = await db.execute(select(LineGroup).where(LineGroup.line_group_id == group_id))
                group = res.scalar_one_or_none()
                if group:
                    if group.farm_id:
                        farm_id = group.farm_id
                    else:
                        group_info = line_service.get_group_summary(group_id)
                        latest_name = group_info.get("groupName")
                        if latest_name:
                            group.group_name = latest_name
                            from models.models import Farm
                            res_farm = await db.execute(select(Farm).where(Farm.name == latest_name))
                            farm = res_farm.scalar_one_or_none()
                            if farm:
                                group.farm_id = farm.id
                                farm_id = farm.id
                        await db.commit()
                    
            if not farm_id:
                if getattr(event, 'reply_token', None):
                    line_service.send_reply(event.reply_token, "⚠️ 此群组尚未连结到系统中的任何农场！\n\n请在群组内输入『@link 农场ID』\n例如：@link 1\n\n(Not linked to any farm. Please link by typing @link [ID])")
                return True
                
            if farm_id:
                import urllib.parse
                data_dict = dict(urllib.parse.parse_qsl(event.postback.data))
                action = data_dict.get('action')
                
                # Test Handlers
                if action == 'test_11am':
                    from services.scheduler import schedule_watering_task
                    background_tasks.add_task(schedule_watering_task)
                    line_service.send_reply(event.reply_token, "🧪 已触发 11AM 浇水测试 (Triggered 11AM test)")
                elif action == 'test_6pm':
                    from services.scheduler import check_missing_work_6pm
                    background_tasks.add_task(check_missing_work_6pm)
                    line_service.send_reply(event.reply_token, "🧪 已触发 6PM 追查进度测试 (Triggered 6PM test)")
                elif action == 'test_7pm':
                    from services.scheduler import generate_evening_summary_7pm
                    background_tasks.add_task(generate_evening_summary_7pm)
                    line_service.send_reply(event.reply_token, "🧪 已触发 7PM 总结测试 (Triggered 7PM test)")
                elif action == 'test_monday':
                    from services.scheduler import create_weekly_health_check_tasks
                    background_tasks.add_task(create_weekly_health_check_tasks)
                    line_service.send_reply(event.reply_token, "🧪 已触发 周一拍照任务生成测试 (Triggered Monday test)")
                
                elif action == 'show_tasks':
                    from models.models import Task, FarmZone
                    from sqlalchemy.orm import selectinload
                    from datetime import datetime, timezone
                    
                    # Start of today (UTC approximate)
                    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
                    
                    query = select(Task).options(selectinload(Task.zone)).where(
                        Task.farm_id == farm_id, 
                        Task.due_date >= today_start
                    ).order_by(Task.due_date.asc(), Task.zone_id.asc(), Task.title.asc())
                    result = await db.execute(query)
                    tasks = result.scalars().all()
                    
                    if not tasks:
                        line_service.send_reply(event.reply_token, "✅ 今天无任务 (No tasks today / Tiada tugas)")
                    else:
                        pending_tasks = {}
                        completed_tasks = {}
                        
                        for t in tasks:
                            z_name = t.zone.name if t.zone else "全局 (Global)"
                            if t.status == "completed":
                                if z_name not in completed_tasks:
                                    completed_tasks[z_name] = []
                                completed_tasks[z_name].append(t)
                            else:
                                if z_name not in pending_tasks:
                                    pending_tasks[z_name] = []
                                pending_tasks[z_name].append(t)
                        
                        reply_lines = ["📋 今日行程总览 (Today's Schedule):\n"]
                        
                        reply_lines.append("【 ⏳ 待办事项 / Pending 】")
                        if not pending_tasks:
                            reply_lines.append(" (全数完成 / All Done! 🎉)")
                        else:
                            for z_name, z_tasks in pending_tasks.items():
                                reply_lines.append(f"\n📍 {z_name}:")
                                for t in z_tasks:
                                    reply_lines.append(f" ⏳ {t.title}")
                                    
                        reply_lines.append("\n====================\n")
                        
                        reply_lines.append("【 ✅ 已完成 / Done 】")
                        if not completed_tasks:
                            reply_lines.append(" (尚无完成事项 / None yet)")
                        else:
                            for z_name, z_tasks in completed_tasks.items():
                                reply_lines.append(f"\n📍 {z_name}:")
                                for t in z_tasks:
                                    reply_lines.append(f" ✅ {t.title}")
                                
                        reply_lines.append("\n👇 请选择下方区域来回报进度:")
                        reply = "\n".join(reply_lines).strip()
                        
                        # Send the text overview
                        line_service.send_text_message(target_id, reply)
                        
                        # Send the zone carousel to reply token
                        res = await db.execute(select(FarmZone).where(FarmZone.farm_id == farm_id))
                        zones = res.scalars().all()
                        if zones:
                            zone_list = [{'id': z.id, 'name': z.name} for z in zones]
                            line_service.send_carousel_zones(event.reply_token, zone_list)
                            
                elif action == 'done_init':
                    from models.models import FarmZone
                    res = await db.execute(select(FarmZone).where(FarmZone.farm_id == farm_id))
                    zones = res.scalars().all()
                    if not zones:
                        line_service.send_reply(event.reply_token, "⚠️ 没有找到任何区域设定。")
                    else:
                        zone_list = [{'id': z.id, 'name': z.name} for z in zones]
                        line_service.send_carousel_zones(event.reply_token, zone_list)
                        
                elif action == 'zone_selected':
                    zone_id = int(data_dict.get('zone_id'))
                    from models.models import Task, FarmZone
                    from sqlalchemy.orm import selectinload
                    query = select(Task).where(
                        Task.farm_id == farm_id, 
                        Task.zone_id == zone_id,
                        Task.status != "completed"
                    ).order_by(Task.due_date.asc())
                    res = await db.execute(query)
                    tasks = res.scalars().all()
                    
                    res_zone = await db.execute(select(FarmZone).where(FarmZone.id == zone_id))
                    zone_name = res_zone.scalar_one().name
                    
                    if not tasks:
                        line_service.send_reply(event.reply_token, f"✅ [{zone_name}] 没有待办任务 (No pending tasks / Tiada tugas yang belum selesai / လုပ်ဆောင်ရန်မရှိပါ / কোন কাজ বাকি নেই)")
                    else:
                        task_list = [{'id': t.id, 'title': t.title} for t in tasks]
                        line_service.send_quick_reply_tasks(event.reply_token, task_list, zone_name)
                        
                elif action == 'task_selected':
                    task_id = int(data_dict.get('task_id'))
                    from models.models import Task
                    res = await db.execute(select(Task).where(Task.id == task_id))
                    t = res.scalar_one_or_none()
                    if t:
                        t.status = "completed"
                        t.completed_at = datetime.now(timezone.utc)
                        await db.commit()
                        line_service.send_reply(event.reply_token, f"✅ 已完成 (Done / Selesai / ပြီးပြီ / সম্পন্ন)! \n{t.title}")
                        
                elif action == 'supply_init':
                    from models.models import InventoryItem
                    res = await db.execute(select(InventoryItem).where(InventoryItem.farm_id == farm_id))
                    items = res.scalars().all()
                    if not items:
                        line_service.send_reply(event.reply_token, f"📦 仓库为空 (Inventory empty / Stok kosong / ကုန်ပစ္စည်းမရှိပါ / স্টক খালি) - Debug: FarmID={farm_id}")
                    else:
                        item_list = [{'id': i.id, 'name': i.name, 'quantity': i.quantity, 'unit': i.unit} for i in items]
                        line_service.send_carousel_inventory(event.reply_token, item_list)
                        
                elif action == 'supply_selected':
                    item_id = int(data_dict.get('item_id'))
                    from models.models import InventoryItem
                    res = await db.execute(select(InventoryItem).where(InventoryItem.id == item_id))
                    it = res.scalar_one_or_none()
                    if it:
                        line_service.send_quick_reply_quantities(event.reply_token, it.name, item_id)
                        
                elif action == 'delivery_init':
                    reply = "照片收到前，请先上传出货单/收据的照片 📷\nPlease upload a photo of the delivery receipt 📷\nSila muat naik gambar resit penghantaran 📷\nပို့ဆောင်မှု ပြေစာ ဓာတ်ပုံကို တင်ပေးပါ 📷\nঅনুগ্রহ করে ডেলিভারি রসিদের একটি ছবি আপলোড করুন 📷"
                    _bot_states[target_id] = {"action": "report_harvest_photo"}
                    line_service.send_reply(event.reply_token, reply)
                        
                elif action == 'qty_selected':
                    item_id = int(data_dict.get('item_id'))
                    qty = int(data_dict.get('qty'))
                    from models.models import InventoryItem
                    res = await db.execute(select(InventoryItem).where(InventoryItem.id == item_id))
                    it = res.scalar_one_or_none()
                    if it:
                        line_service.send_quick_reply_units(event.reply_token, it.name, item_id, qty, it.unit)
                        
                elif action == 'unit_selected':
                    item_id = int(data_dict.get('item_id'))
                    qty = float(data_dict.get('qty'))
                    unit = data_dict.get('unit')
                    from models.models import InventoryItem
                    res = await db.execute(select(InventoryItem).where(InventoryItem.id == item_id))
                    it = res.scalar_one_or_none()
                    if it:
                        it.quantity = max(0, it.quantity - qty)
                        await db.commit()
                        line_service.send_reply(event.reply_token, f"✅ 已记录使用 (Recorded usage): \n{it.name} -{qty} {unit}")
                        
                elif action == 'problem_init':
                    line_service.send_camera_quick_reply(event.reply_token)

    return "OK"

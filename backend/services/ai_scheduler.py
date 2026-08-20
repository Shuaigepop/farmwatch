import json
import asyncio
import traceback
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import models
from services.ai_service import ai_service
from google.genai import types


def _call_gemini_sync(prompt: str, json_mode: bool = False):
    """Synchronous wrapper for Gemini API call with retry."""
    config = None
    if json_mode:
        config = types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    response = ai_service.client.models.generate_content(
        model='gemini-3.5-flash',
        contents=[prompt],
        config=config
    )
    return response.text


def _clean_json(text: str) -> str:
    """Clean markdown formatting from JSON responses."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


async def generate_daily_schedule(farm_id: int, db: AsyncSession):
    """Generate daily schedule using multi-agent AI approach.
    
    Uses asyncio.to_thread to avoid blocking the event loop 
    during synchronous Gemini API calls.
    """
    try:
        # 1. Fetch recent photos with issues
        yesterday = datetime.utcnow() - timedelta(days=1)
        res = await db.execute(select(models.Photo).where(
            models.Photo.farm_id == farm_id,
            models.Photo.captured_at >= yesterday,
            models.Photo.health_status.in_(["warning", "critical"])
        ))
        bad_photos = res.scalars().all()
        
        photo_summaries = []
        for p in bad_photos:
            photo_summaries.append(f"Zone {p.zone_id}: {p.ai_analysis}")
        
        # 2. Fetch inventory
        inv_res = await db.execute(select(models.InventoryItem).where(
            models.InventoryItem.farm_id == farm_id
        ))
        inventory = inv_res.scalars().all()
        inv_data = [{"name": i.name, "quantity": i.quantity, "unit": i.unit} for i in inventory]
        
        # 3. Fetch pending tasks
        tasks_res = await db.execute(select(models.Task).where(
            models.Task.farm_id == farm_id,
            models.Task.status == "pending"
        ))
        pending_tasks = tasks_res.scalars().all()
        task_data = [{"title": t.title, "description": t.description, "zone_id": t.zone_id} for t in pending_tasks]

        # 4. Fetch impending harvest plans
        harvest_res = await db.execute(select(models.HarvestPlan).where(
            models.HarvestPlan.farm_id == farm_id,
            models.HarvestPlan.status == "growing"
        ))
        growing_plans = harvest_res.scalars().all()
        today_date = datetime.utcnow().date()
        impending_harvests = []
        for plan in growing_plans:
            if plan.expected_harvest_date:
                days_left = (plan.expected_harvest_date - today_date).days
                if days_left <= 3:
                    impending_harvests.append({
                        "crop": plan.crop_name,
                        "zone": plan.area_or_zone,
                        "days_left": days_left
                    })

        print(f"[AI Scheduler] Farm {farm_id}: {len(bad_photos)} bad photos, {len(inv_data)} inv items, {len(task_data)} pending tasks, {len(impending_harvests)} impending harvests")

        # Agent 1: Disease Expert (run in thread to avoid blocking)
        prompt1 = f"""【植物病理专家 AI】
最近24小时有以下警告照片分析：
{photo_summaries if photo_summaries else '没有异常照片'}
请根据这些状况提供简短建议（3-5条），建议农场今天应该执行哪些任务来处理这些病害问题？
如果没有异常照片，请回覆「目前无病害警告，建议日常巡检」。"""

        print("[AI Scheduler] Calling Agent 1: Disease Expert...")
        agent1_suggestion = await asyncio.to_thread(_call_gemini_sync, prompt1)
        print(f"[AI Scheduler] Agent 1 done. Length: {len(agent1_suggestion)}")

        # Agent 2: Inventory Expert (run in thread)
        prompt2 = f"""【库存管理专家 AI】
目前库存状况：
{inv_data if inv_data else '库存资料为空'}
请分析是否有极低库存的项目，并简短建议今天是否需要盘点或采购任务？（3-5条）
如果库存为空，请回覆「无库存数据，建议进行首次盘点」。"""

        print("[AI Scheduler] Calling Agent 2: Inventory Expert...")
        agent2_suggestion = await asyncio.to_thread(_call_gemini_sync, prompt2)
        print(f"[AI Scheduler] Agent 2 done. Length: {len(agent2_suggestion)}")

        # Agent 3: Coordinator (run in thread, JSON mode)
        prompt3 = f"""【农场大管家 AI】
请根据以下信息，安排今天的任务行程。
疾病专家建议：{agent1_suggestion}
库存专家建议：{agent2_suggestion}
目前的待办任务：{task_data}
即将采收的作物（需要在今天排入采收任务）：{impending_harvests if impending_harvests else '无即将采收的作物'}

请输出一个 JSON 阵列（Array），包含今天要执行的任务列表（5-8个任务即可）。
每个任务必须是一个 JSON 对象，包含以下栏位：
- "title": 任务标题（若采收，请注明「采收 [作物]」）
- "zone_id": 区域ID（如果有对应，可填整数；若无特定区域可填 null）
- "description": 任务详细说明（简短30字以内）
只回传纯 JSON 阵列，不要包含其他文字。"""

        print("[AI Scheduler] Calling Agent 3: Coordinator...")
        coordinator_response = await asyncio.to_thread(_call_gemini_sync, prompt3, True)
        print(f"[AI Scheduler] Agent 3 done. Length: {len(coordinator_response)}")
        
        tasks_json = _clean_json(coordinator_response)
        
        # Validate JSON before saving
        parsed = json.loads(tasks_json)
        if not isinstance(parsed, list):
            # If it returned an object with a key, try to extract the array
            if isinstance(parsed, dict):
                for key in parsed:
                    if isinstance(parsed[key], list):
                        parsed = parsed[key]
                        tasks_json = json.dumps(parsed, ensure_ascii=False)
                        break
            else:
                raise ValueError(f"Expected JSON array, got {type(parsed)}")
        
        print(f"[AI Scheduler] Parsed {len(parsed)} tasks successfully")

        today_str = datetime.utcnow().strftime("%Y-%m-%d")
        
        # Save to ProposedSchedule
        exist_res = await db.execute(select(models.ProposedSchedule).where(
            models.ProposedSchedule.farm_id == farm_id,
            models.ProposedSchedule.date == today_str
        ))
        existing = exist_res.scalar_one_or_none()
        
        if existing:
            existing.tasks_json = tasks_json
            existing.status = "draft"
        else:
            new_schedule = models.ProposedSchedule(
                farm_id=farm_id,
                date=today_str,
                tasks_json=tasks_json,
                status="draft"
            )
            db.add(new_schedule)
        
        await db.commit()
        print(f"[AI Scheduler] Schedule saved for farm {farm_id}, date {today_str}")
        return parsed
        
    except Exception as e:
        print(f"[AI Scheduler ERROR] {e}")
        traceback.print_exc()
        raise

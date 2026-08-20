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
    """Generate daily schedule using a rule-based approach + AI formatting.
    
    This ensures tasks are strictly based on SOPs, crop cycles, and real events,
    while AI is only used to organize and present them nicely.
    """
    try:
        today_date = datetime.utcnow().date()
        current_month = today_date.month
        current_weekday = today_date.weekday() # 0 = Mon, 6 = Sun
        
        raw_tasks = []
        
        # 1. Fetch SOPs (RecurringTasks)
        # In a real app we'd parse cron expression. For now, we'll just fetch active ones
        # and assume they are daily, or if we had a proper cron parser we'd check it.
        # As a simplification for this MVP, we include all active recurring tasks.
        sops_res = await db.execute(select(models.RecurringTask).where(
            models.RecurringTask.farm_id == farm_id,
            models.RecurringTask.is_active == True
        ))
        for sop in sops_res.scalars().all():
            raw_tasks.append({
                "title": f"[日常] {sop.title}",
                "zone_id": sop.zone_id,
                "description": sop.description
            })

        # 2. Fetch Fertilizer Schedules for current month
        fert_res = await db.execute(select(models.FertilizerSchedule).where(
            models.FertilizerSchedule.farm_id == farm_id,
            models.FertilizerSchedule.month == current_month
        ))
        for fert in fert_res.scalars().all():
            raw_tasks.append({
                "title": "[施肥] 本月排程",
                "zone_id": None,
                "description": f"施放 {fert.fertilizer_name}, 数量: {fert.quantity} {fert.unit}"
            })

        # 3. Fetch ZoneCropPlans
        crop_res = await db.execute(select(models.ZoneCropPlan).where(
            models.ZoneCropPlan.farm_id == farm_id
        ))
        for plan in crop_res.scalars().all():
            if plan.status == "growing" and plan.expected_harvest_date:
                days_left = (plan.expected_harvest_date - today_date).days
                if days_left <= 3 and days_left > 0:
                    raw_tasks.append({
                        "title": f"[采收预警] {plan.crop_name}",
                        "zone_id": plan.zone_id,
                        "description": f"还有 {days_left} 天采收, 请准备采收工具"
                    })
                elif days_left <= 0:
                    raw_tasks.append({
                        "title": f"[今日采收] {plan.crop_name}",
                        "zone_id": plan.zone_id,
                        "description": "已经可以采收！"
                    })
            elif plan.status == "harvesting" and plan.harvest_end_date:
                days_over = (today_date - plan.harvest_end_date).days
                if days_over >= 0:
                    raw_tasks.append({
                        "title": f"[采收结束] {plan.crop_name}",
                        "zone_id": plan.zone_id,
                        "description": "采收期已结束, 请清理残株并准备翻土"
                    })
            elif plan.status == "preparing":
                next_crop = f" (准备种: {plan.next_crop_name})" if plan.next_crop_name else ""
                raw_tasks.append({
                    "title": f"[翻土准备]",
                    "zone_id": plan.zone_id,
                    "description": f"执行翻土、施底肥、消毒作业{next_crop}"
                })

        # 4. Fetch Inventory Alerts
        inv_res = await db.execute(select(models.InventoryItem).where(
            models.InventoryItem.farm_id == farm_id
        ))
        for item in inv_res.scalars().all():
            if item.quantity < 50: 
                raw_tasks.append({
                    "title": f"[库存警告] {item.name}",
                    "zone_id": None,
                    "description": f"库存偏低 ({item.quantity} {item.unit}), 请尽快盘点或采购"
                })

        # 5. Fetch Photo Issues
        yesterday = datetime.utcnow() - timedelta(days=1)
        res = await db.execute(select(models.Photo).where(
            models.Photo.farm_id == farm_id,
            models.Photo.captured_at >= yesterday,
            models.Photo.health_status.in_(["warning", "critical"])
        ))
        for p in res.scalars().all():
            raw_tasks.append({
                "title": "[异常处理]",
                "zone_id": p.zone_id,
                "description": f"发现异常: {p.ai_analysis[:20]}..."
            })

        print(f"[AI Scheduler] Farm {farm_id}: Gathered {len(raw_tasks)} rule-based tasks")

        # If no tasks generated by rules, fallback to a general task
        if not raw_tasks:
            raw_tasks.append({
                "title": "[日常巡检]",
                "zone_id": None,
                "description": "全区巡视，检查是否有虫害或缺水状况"
            })

        print(f"[AI Scheduler] Parsed {len(raw_tasks)} tasks successfully (Deterministic)")
        
        parsed = raw_tasks
        tasks_json = json.dumps(parsed, ensure_ascii=False)

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

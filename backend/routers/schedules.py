from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
import json
from pydantic import BaseModel
from typing import List, Optional

from deps import get_db
from models import models
from services.ai_scheduler import generate_daily_schedule
from services.line_service import line_service

router = APIRouter(prefix="/api/schedules", tags=["Schedules"])

class ApprovedTask(BaseModel):
    title: str
    zone_id: Optional[int] = None
    description: str
    target_role: str = 'worker'

class ApproveRequest(BaseModel):
    tasks: List[ApprovedTask]

@router.post("/{farm_id}/generate")
async def generate_schedule(farm_id: int, db: AsyncSession = Depends(get_db)):
    try:
        tasks = await generate_daily_schedule(farm_id, db)
        return {"message": "Schedule generated", "tasks": tasks}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"AI schedule generation failed: {str(e)}")

@router.get("/{farm_id}/today")
async def get_today_schedule(farm_id: int, db: AsyncSession = Depends(get_db)):
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    result = await db.execute(select(models.ProposedSchedule).where(
        models.ProposedSchedule.farm_id == farm_id,
        models.ProposedSchedule.date == today_str
    ))
    schedule = result.scalar_one_or_none()
    
    if not schedule:
        return {"status": "none"}
        
    return {
        "status": schedule.status,
        "date": schedule.date,
        "tasks": json.loads(schedule.tasks_json)
    }

@router.post("/{farm_id}/approve")
async def approve_schedule(farm_id: int, req: ApproveRequest, db: AsyncSession = Depends(get_db)):
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    result = await db.execute(select(models.ProposedSchedule).where(
        models.ProposedSchedule.farm_id == farm_id,
        models.ProposedSchedule.date == today_str
    ))
    schedule = result.scalar_one_or_none()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
        
    schedule.status = "approved"
    schedule.tasks_json = json.dumps([t.model_dump() for t in req.tasks])
    
    # Create Task records
    for t in req.tasks:
        new_task = models.Task(
            farm_id=farm_id,
            zone_id=t.zone_id,
            title=t.title,
            description=t.description,
            stage="general",
            status="pending",
            target_role=t.target_role if hasattr(t, 'target_role') else 'worker'
        )
        db.add(new_task)
    
    await db.commit()
    
    worker_tasks = []
    foreman_tasks = []
    for t in req.tasks:
        target_role = t.target_role if hasattr(t, 'target_role') else 'worker'
        if target_role == 'foreman':
            foreman_tasks.append(t.title)
        else:
            worker_tasks.append(t.title)

    # Send notification to LINE
    task_msgs = []
    task_msgs.append("[Worker Tasks]")
    for i, title in enumerate(worker_tasks):
        task_msgs.append(f"{i+1}. {title}")
        
    task_msgs.append("")
    task_msgs.append("[Foreman Tasks]")
    for i, title in enumerate(foreman_tasks):
        task_msgs.append(f"{i+1}. {title}")

    try:
        from services.ai_service import ai_service
        if worker_tasks:
            translations_str = await ai_service.translate_tasks(worker_tasks)
            translations_str = translations_str.strip()
            if translations_str.startswith("```json"):
                translations_str = translations_str[7:]
            elif translations_str.startswith("```"):
                translations_str = translations_str[3:]
            if translations_str.endswith("```"):
                translations_str = translations_str[:-3]
            translations = json.loads(translations_str.strip())
            
            task_msgs.append("")
            task_msgs.append("[ID] Tugas Pekerja:")
            for i, tr in enumerate(translations):
                task_msgs.append(f"{i+1}. {tr.get('id', '')}")
                
            task_msgs.append("")
            task_msgs.append("[MS] Tugasan Pekerja:")
            for i, tr in enumerate(translations):
                task_msgs.append(f"{i+1}. {tr.get('ms', '')}")
                
            task_msgs.append("")
            task_msgs.append("[MM] Burmese:")
            for i, tr in enumerate(translations):
                task_msgs.append(f"{i+1}. {tr.get('mm', '')}")

    except Exception as e:
        print(f"Translation failed: {e}")

    msg_text = "今日AI派发任务已核准：\n" + "\n".join(task_msgs)
    
    # Find group ID for this farm
    group_res = await db.execute(select(models.LineGroup).where(models.LineGroup.farm_id == farm_id))
    group = group_res.scalar_one_or_none()
    
    if group:
        await line_service.send_text_message(group.line_group_id, msg_text)
        
    return {"message": "Schedule approved and tasks created"}

@router.post("/{farm_id}/revert")
async def revert_schedule(farm_id: int, db: AsyncSession = Depends(get_db)):
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    result = await db.execute(select(models.ProposedSchedule).where(
        models.ProposedSchedule.farm_id == farm_id,
        models.ProposedSchedule.date == today_str
    ))
    schedule = result.scalar_one_or_none()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
        
    schedule.status = "draft"
    await db.commit()
    return {"message": "Schedule reverted to draft"}

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

class ApproveRequest(BaseModel):
    tasks: List[ApprovedTask]

@router.post("/{farm_id}/generate")
async def generate_schedule(farm_id: int, db: AsyncSession = Depends(get_db)):
    tasks = await generate_daily_schedule(farm_id, db)
    return {"message": "Schedule generated", "tasks": tasks}

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
            status="pending"
        )
        db.add(new_task)
    
    await db.commit()
    
    # Send notification to LINE
    task_msgs = []
    for i, t in enumerate(req.tasks):
        task_msgs.append(f"{i+1}. {t.title}")
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

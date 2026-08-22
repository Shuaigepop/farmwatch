from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from database import AsyncSessionLocal
from models.models import Task, User, RecurringTask
from schemas import TaskCreate, TaskUpdate, TaskResponse
from deps import get_db, get_current_user, require_role
from datetime import datetime

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

@router.get("/", response_model=List[TaskResponse])
async def list_tasks(
    farm_id: Optional[int] = None,
    zone_id: Optional[int] = None,
    status: Optional[str] = None,
    target_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 獲取任務列表 (Get task list)
    query = select(Task)
    
    if current_user.role == "leader":
        if not current_user.farm_id:
            return []
        query = query.where(Task.farm_id == current_user.farm_id)
    elif farm_id:
        query = query.where(Task.farm_id == farm_id)
        
    if status:
        query = query.where(Task.status == status)
        
    if zone_id:
        query = query.where(Task.zone_id == zone_id)
        
    if target_date:
        from sqlalchemy import cast, Date, or_
        from datetime import datetime
        try:
            date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()
            query = query.where(
                or_(
                    cast(Task.created_at, Date) == date_obj,
                    cast(Task.completed_at, Date) == date_obj
                )
            )
        except ValueError:
            pass
            
    result = await db.execute(query.order_by(Task.due_date.asc()))
    return result.scalars().all()

@router.post("/", response_model=TaskResponse)
async def create_task(
    task_in: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["boss", "supervisor"]))
):
    # 建立任務 (Create task)
    new_task = Task(**task_in.model_dump())
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    return new_task

@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_in: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 更新任務 (Update task)
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    if current_user.role == "leader" and task.farm_id != current_user.farm_id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    update_data = task_in.model_dump(exclude_unset=True)
    just_completed = False
    if "status" in update_data and update_data["status"] == "completed" and task.status != "completed":
        task.completed_at = datetime.utcnow()
        just_completed = True
        
    for key, value in update_data.items():
        setattr(task, key, value)
        
    await db.commit()
    await db.refresh(task)
    
    # Check if this was a planting task that just got completed
    if just_completed and task.zone_id:
        title_lower = (task.title or "").lower()
        if "plant" in title_lower or "种植" in title_lower or "種植" in title_lower:
            # It's a planting task! Let's find if a crop matches
            # We need to import Crop and HarvestPlan, hopefully they are in models
            from models.models import Crop, HarvestPlan, FarmZone
            from datetime import timedelta
            
            # Find the farm's crops
            crops_res = await db.execute(select(Crop).where(Crop.farm_id == task.farm_id))
            crops = crops_res.scalars().all()
            
            matched_crop = None
            for c in crops:
                if c.name.lower() in title_lower:
                    matched_crop = c
                    break
            
            if matched_crop:
                # Get the zone name for the area_or_zone field
                zone_res = await db.execute(select(FarmZone).where(FarmZone.id == task.zone_id))
                zone = zone_res.scalar_one_or_none()
                zone_name = zone.name if zone else str(task.zone_id)
                
                # Check if a pending_verification or growing plan already exists for this crop and zone
                existing_plan_res = await db.execute(select(HarvestPlan).where(
                    HarvestPlan.farm_id == task.farm_id,
                    HarvestPlan.crop_name == matched_crop.name,
                    HarvestPlan.area_or_zone == zone_name,
                    HarvestPlan.status.in_(["pending_verification", "growing"])
                ))
                existing_plan = existing_plan_res.scalar_one_or_none()
                
                if not existing_plan:
                    # Create a new HarvestPlan in pending_verification status
                    new_plan = HarvestPlan(
                        farm_id=task.farm_id,
                        crop_name=matched_crop.name,
                        planted_date=datetime.utcnow().date(),
                        expected_harvest_date=datetime.utcnow().date() + timedelta(days=matched_crop.grow_days),
                        area_or_zone=zone_name,
                        status="pending_verification",
                        notes=f"Auto-generated from planting task #{task.id}"
                    )
                    db.add(new_plan)
                    await db.commit()
    
    return task

@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["boss"]))
):
    # 删除任务 (Delete task)
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    await db.delete(task)
    await db.commit()
    return {"status": "success"}

from pydantic import BaseModel

class RecurringTaskCreate(BaseModel):
    farm_id: int
    zone_id: Optional[int] = None
    title: str
    description: str
    cron_expression: str = '0 6 * * *'
    target_role: str = 'worker'
    is_active: bool = True

@router.get("/recurring")
async def list_recurring_tasks(
    farm_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(RecurringTask).where(RecurringTask.farm_id == farm_id))
    return result.scalars().all()

@router.post("/recurring")
async def create_recurring_task(
    task_in: RecurringTaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["boss", "supervisor"]))
):
    new_task = RecurringTask(**task_in.model_dump())
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    return new_task

@router.delete("/recurring/{task_id}")
async def delete_recurring_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["boss"]))
):
    result = await db.execute(select(RecurringTask).where(RecurringTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Recurring task not found")
        
    await db.delete(task)
    await db.commit()
    return {"status": "success"}

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from database import AsyncSessionLocal
from models.models import Task, User
from schemas import TaskCreate, TaskUpdate, TaskResponse
from deps import get_db, get_current_user, require_role
from datetime import datetime

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

@router.get("/", response_model=List[TaskResponse])
async def list_tasks(
    farm_id: Optional[int] = None,
    zone_id: Optional[int] = None,
    status: Optional[str] = None,
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
    if "status" in update_data and update_data["status"] == "completed" and task.status != "completed":
        task.completed_at = datetime.utcnow()
        
    for key, value in update_data.items():
        setattr(task, key, value)
        
    await db.commit()
    await db.refresh(task)
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

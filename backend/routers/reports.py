from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from deps import get_db, get_current_user, require_role
from models.models import User, DailyReport
from schemas import DailyReportResponse

router = APIRouter(prefix="/api/reports", tags=["reports"])

@router.get("/daily", response_model=List[DailyReportResponse])
async def list_reports(
    farm_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "boss" and current_user.farm_id:
        # Enforce their own farm
        farm_id = current_user.farm_id
        
    query = select(DailyReport).order_by(DailyReport.created_at.desc())
    if farm_id:
        query = query.where(DailyReport.farm_id == farm_id)
        
    result = await db.execute(query)
    reports = result.scalars().all()
    return reports
@router.post("/{farm_id}/generate")
async def generate_report_manually(
    farm_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "boss" and current_user.farm_id != farm_id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    from models.models import Farm, LineGroup, Task, Photo, InventoryItem
    from services.ai_service import ai_service
    from services.line_service import line_service
    from sqlalchemy import and_
    from datetime import datetime, timedelta, timezone
    import json
    
    # Check farm
    res = await db.execute(select(Farm).where(Farm.id == farm_id))
    farm = res.scalar_one_or_none()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
        
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    
    # Fetch active tasks
    task_res = await db.execute(select(Task).where(and_(Task.farm_id == farm.id, Task.status != "completed")))
    tasks = [{"title": t.title, "stage": t.stage, "status": t.status} for t in task_res.scalars().all()]
    
    # Fetch inventory items
    inv_res = await db.execute(select(InventoryItem).where(InventoryItem.farm_id == farm.id))
    inventory = [{"name": i.name, "quantity": i.quantity, "unit": i.unit} for i in inv_res.scalars().all()]
    
    # Fetch recent photos
    photo_res = await db.execute(select(Photo).where(and_(Photo.farm_id == farm.id, Photo.captured_at >= yesterday)))
    photos = [{"status": p.health_status, "ai_notes": p.ai_analysis} for p in photo_res.scalars().all()]
    
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    analyst_report = await ai_service.analyze_data(inventory, tasks)
    summary_text = await ai_service.generate_daily_summary(date_str, analyst_report, tasks, photos)
    
    report = DailyReport(
        report_date=datetime.now().strftime("%Y-%m-%d"),
        farm_id=farm.id,
        summary_json=json.dumps({"text": summary_text}, ensure_ascii=False),
        sent=True,
        sent_at=datetime.now(timezone.utc)
    )
    db.add(report)
    await db.commit()
    
    # Send to line
    groups_result = await db.execute(select(LineGroup.line_group_id))
    all_groups = groups_result.scalars().all()
    for group_id in all_groups:
        line_service.send_text_message(group_id, f"📊 【FarmWatch 大管家日报 - 手动生成】\n\n{summary_text}")
        
    return {"message": "Report generated successfully", "report_text": summary_text}

@router.get('/{farm_id}/fertilizer-budget')
async def get_fertilizer_budget(
    farm_id: int,
    month: int = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from models.models import FertilizerSchedule
    from datetime import datetime
    if not month:
        month = datetime.now().month
        
    result = await db.execute(select(FertilizerSchedule).where(
        FertilizerSchedule.farm_id == farm_id,
        FertilizerSchedule.month == month
    ))
    schedules = result.scalars().all()
    
    total_cost = 0
    items = []
    for s in schedules:
        cost = s.quantity * s.cost_per_unit
        total_cost += cost
        items.append({
            'name': s.fertilizer_name,
            'quantity': s.quantity,
            'unit': s.unit,
            'cost_per_unit': s.cost_per_unit,
            'total_cost': cost
        })
        
    return {
        'month': month,
        'items': items,
        'total_budget': total_cost
    }

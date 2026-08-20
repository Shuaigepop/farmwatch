from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime, date, timedelta
from pydantic import BaseModel
from typing import List, Optional

from deps import get_db
from models import models

router = APIRouter(prefix="/api/farms", tags=["Zone Plans"])

class ZoneCropPlanCreate(BaseModel):
    zone_id: int
    crop_id: int
    planted_date: date

class ZoneCropPlanUpdate(BaseModel):
    status: Optional[str] = None
    next_crop_name: Optional[str] = None
    last_harvest_kg: Optional[float] = None
    notes: Optional[str] = None

@router.get("/{farm_id}/zone-plans")
async def get_zone_plans(farm_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.ZoneCropPlan)
        .where(models.ZoneCropPlan.farm_id == farm_id)
        .options(selectinload(models.ZoneCropPlan.zone), selectinload(models.ZoneCropPlan.crop))
    )
    plans = result.scalars().all()
    
    response = []
    for plan in plans:
        # Calculate days until harvest or days since planting
        days_left = None
        if plan.expected_harvest_date:
            days_left = (plan.expected_harvest_date - datetime.utcnow().date()).days
            
        response.append({
            "id": plan.id,
            "farm_id": plan.farm_id,
            "zone_id": plan.zone_id,
            "zone_name": plan.zone.name if plan.zone else None,
            "parent_zone": plan.zone.parent_zone if plan.zone else None,
            "crop_id": plan.crop_id,
            "crop_name": plan.crop_name,
            "planted_date": plan.planted_date,
            "expected_harvest_date": plan.expected_harvest_date,
            "harvest_end_date": plan.harvest_end_date,
            "status": plan.status,
            "next_crop_name": plan.next_crop_name,
            "last_harvest_kg": plan.last_harvest_kg,
            "notes": plan.notes,
            "days_left": days_left
        })
    return response

@router.post("/{farm_id}/zone-plans")
async def create_zone_plan(farm_id: int, plan: ZoneCropPlanCreate, db: AsyncSession = Depends(get_db)):
    # Verify zone
    zone_result = await db.execute(select(models.FarmZone).where(models.FarmZone.id == plan.zone_id, models.FarmZone.farm_id == farm_id))
    zone = zone_result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
        
    # Verify crop
    crop_result = await db.execute(select(models.Crop).where(models.Crop.id == plan.crop_id, models.Crop.farm_id == farm_id))
    crop = crop_result.scalar_one_or_none()
    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found")
        
    # Calculate dates
    expected_harvest_date = plan.planted_date + timedelta(days=crop.grow_days)
    harvest_end_date = expected_harvest_date + timedelta(days=crop.harvest_duration_days)
    
    # Check if a plan already exists for this zone
    existing_result = await db.execute(select(models.ZoneCropPlan).where(models.ZoneCropPlan.zone_id == plan.zone_id))
    existing = existing_result.scalar_one_or_none()
    
    if existing:
        existing.crop_id = plan.crop_id
        existing.crop_name = crop.name
        existing.planted_date = plan.planted_date
        existing.expected_harvest_date = expected_harvest_date
        existing.harvest_end_date = harvest_end_date
        existing.status = "planted" if plan.planted_date == datetime.utcnow().date() else "growing"
        existing.next_crop_name = None
        existing.last_harvest_kg = None
        new_plan = existing
    else:
        new_plan = models.ZoneCropPlan(
            farm_id=farm_id,
            zone_id=plan.zone_id,
            crop_id=plan.crop_id,
            crop_name=crop.name,
            planted_date=plan.planted_date,
            expected_harvest_date=expected_harvest_date,
            harvest_end_date=harvest_end_date,
            status="planted" if plan.planted_date == datetime.utcnow().date() else "growing"
        )
        db.add(new_plan)
        
    await db.commit()
    return {"message": "Zone crop plan created/updated successfully"}

@router.put("/zone-plans/{plan_id}")
async def update_zone_plan(plan_id: int, update: ZoneCropPlanUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.ZoneCropPlan).where(models.ZoneCropPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Zone crop plan not found")
        
    if update.status: plan.status = update.status
    if update.next_crop_name is not None: plan.next_crop_name = update.next_crop_name
    if update.last_harvest_kg is not None: plan.last_harvest_kg = update.last_harvest_kg
    if update.notes is not None: plan.notes = update.notes
    
    await db.commit()
    return {"message": "Zone crop plan updated"}

@router.post("/zone-plans/{plan_id}/action/{action}")
async def zone_plan_action(plan_id: int, action: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.ZoneCropPlan).where(models.ZoneCropPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Zone crop plan not found")
        
    if action == "harvest":
        plan.status = "harvesting"
    elif action == "finish":
        plan.status = "preparing"
    elif action == "clear":
        plan.status = "idle"
        plan.crop_id = None
        plan.crop_name = None
        plan.planted_date = None
        plan.expected_harvest_date = None
        plan.harvest_end_date = None
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
        
    await db.commit()
    return {"message": f"Action '{action}' applied successfully"}

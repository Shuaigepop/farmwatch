from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from models.models import User, InventoryItem, HarvestPlan
from schemas import InventoryItemCreate, InventoryItemUpdate, InventoryItemResponse, HarvestPlanCreate, HarvestPlanUpdate, HarvestPlanResponse
from deps import get_db, get_current_user, require_role

router = APIRouter(prefix="/api/inventory", tags=["inventory"])

@router.get("/{farm_id}", response_model=List[InventoryItemResponse])
async def list_inventory(
    farm_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Enforce farm isolation
    if current_user.role != "boss" and current_user.farm_id != farm_id:
        raise HTTPException(status_code=403, detail="Not authorized for this farm")
        
    query = select(InventoryItem).where(InventoryItem.farm_id == farm_id)
    result = await db.execute(query)
    items = result.scalars().all()
    return items

@router.get("/debug/all")
async def list_all_inventory_debug(db: AsyncSession = Depends(get_db)):
    # DEBUG ENDPOINT: Dumps all items in the database
    result = await db.execute(select(InventoryItem))
    items = result.scalars().all()
    return items

@router.post("/{farm_id}", response_model=InventoryItemResponse)
async def create_inventory_item(
    farm_id: int,
    item_in: InventoryItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["boss", "supervisor"]))
):
    if current_user.role != "boss" and current_user.farm_id != farm_id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    new_item = InventoryItem(**item_in.model_dump(), farm_id=farm_id)
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    return new_item

@router.put("/{item_id}", response_model=InventoryItemResponse)
async def update_inventory_item(
    item_id: int,
    item_in: InventoryItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["boss", "supervisor"]))
):
    res = await db.execute(select(InventoryItem).where(InventoryItem.id == item_id))
    item = res.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
        
    if current_user.role != "boss" and current_user.farm_id != item.farm_id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    update_data = item_in.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(item, k, v)
        
    await db.commit()
    await db.refresh(item)
    return item

@router.delete("/{item_id}")
async def delete_inventory_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["boss"]))
):
    res = await db.execute(select(InventoryItem).where(InventoryItem.id == item_id))
    item = res.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
        
    if current_user.farm_id and current_user.farm_id != item.farm_id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    await db.delete(item)
    await db.commit()
    return {"message": "Deleted successfully"}

from models.models import HarvestPlan
from schemas import HarvestPlanCreate, HarvestPlanUpdate, HarvestPlanResponse

@router.get("/harvest/{farm_id}", response_model=List[HarvestPlanResponse])
async def list_harvest_plans(
    farm_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "boss" and current_user.farm_id != farm_id:
        raise HTTPException(status_code=403, detail="Not authorized for this farm")
    query = select(HarvestPlan).where(HarvestPlan.farm_id == farm_id)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/harvest/{farm_id}", response_model=HarvestPlanResponse)
async def create_harvest_plan(
    farm_id: int,
    plan_in: HarvestPlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["boss", "supervisor"]))
):
    if current_user.role != "boss" and current_user.farm_id != farm_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    new_plan = HarvestPlan(**plan_in.model_dump(), farm_id=farm_id)
    db.add(new_plan)
    await db.commit()
    await db.refresh(new_plan)
    return new_plan

@router.put("/harvest/{plan_id}", response_model=HarvestPlanResponse)
async def update_harvest_plan(
    plan_id: int,
    plan_in: HarvestPlanUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["boss", "supervisor"]))
):
    res = await db.execute(select(HarvestPlan).where(HarvestPlan.id == plan_id))
    plan = res.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if current_user.role != "boss" and current_user.farm_id != plan.farm_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    update_data = plan_in.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(plan, k, v)
    await db.commit()
    await db.refresh(plan)
    return plan

@router.delete("/harvest/{plan_id}")
async def delete_harvest_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["boss", "supervisor"]))
):
    res = await db.execute(select(HarvestPlan).where(HarvestPlan.id == plan_id))
    plan = res.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if current_user.role != "boss" and current_user.farm_id != plan.farm_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    await db.delete(plan)
    await db.commit()
    return {"status": "success"}


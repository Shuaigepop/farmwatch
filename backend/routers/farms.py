from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List

from database import AsyncSessionLocal
from models.models import Farm, User, LineGroup, Message, Photo, FarmZone, Crop
from schemas import FarmCreate, FarmResponse, LineGroupLink, LineGroupResponse, FarmZoneCreate, FarmZoneResponse, CropCreate, CropUpdate, CropResponse
from deps import get_db, get_current_user, require_role

router = APIRouter(prefix="/api/farms", tags=["farms"])

@router.get("/", response_model=List[FarmResponse])
async def list_farms(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 獲取農場列表 (Get farm list)
    if current_user.role == "leader":
        if not current_user.farm_id:
            return []
        result = await db.execute(select(Farm).where(Farm.id == current_user.farm_id))
    else:
        result = await db.execute(select(Farm))
    return result.scalars().all()

@router.post("/", response_model=FarmResponse)
async def create_farm(
    farm_in: FarmCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["boss"]))
):
    # 建立農場 - 僅限老闆 (Create farm - Boss only)
    new_farm = Farm(**farm_in.model_dump())
    db.add(new_farm)
    await db.commit()
    await db.refresh(new_farm)
    return new_farm

@router.put("/{farm_id}", response_model=FarmResponse)
async def update_farm(
    farm_id: int,
    farm_in: FarmCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["boss"]))
):
    # 更新農場資訊 (Update farm info)
    result = await db.execute(select(Farm).where(Farm.id == farm_id))
    farm = result.scalar_one_or_none()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
        
    for key, value in farm_in.model_dump().items():
        setattr(farm, key, value)
        
    await db.commit()
    await db.refresh(farm)
    return farm

@router.delete("/{farm_id}")
async def delete_farm(
    farm_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["boss"]))
):
    # 删除农场 (Delete farm)
    result = await db.execute(select(Farm).where(Farm.id == farm_id))
    farm = result.scalar_one_or_none()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    
    await db.delete(farm)
    await db.commit()
    return {"status": "success"}

@router.get("/{farm_id}/stats")
async def farm_stats(
    farm_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 獲取農場統計數據 (Get farm stats)
    if current_user.role == "leader" and current_user.farm_id != farm_id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    msg_count = await db.scalar(select(func.count(Message.id)).where(Message.farm_id == farm_id))
    photo_count = await db.scalar(select(func.count(Photo.id)).where(Photo.farm_id == farm_id))
    
    return {
        "message_count": msg_count,
        "photo_count": photo_count
    }

@router.post("/link-group")
async def link_group(
    link: LineGroupLink,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["boss", "supervisor"]))
):
    # 连结 LINE 群组到农场 (Link LINE group to farm)
    result = await db.execute(select(LineGroup).where(LineGroup.line_group_id == link.line_group_id))
    group = result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(status_code=404, detail="Line group not found")
        
    group.farm_id = link.farm_id
    if link.group_name:
        group.group_name = link.group_name
        
    await db.commit()
    
    # Notify the group
    from services.line_service import line_service
    res_farm = await db.execute(select(Farm).where(Farm.id == link.farm_id))
    farm = res_farm.scalar_one_or_none()
    if farm:
        line_service.send_text_message(group.line_group_id, f"✅ 此群组已由管理员重新连结至【{farm.name}】")
        
    return {"status": "success"}

@router.get("/line-groups", response_model=List[LineGroupResponse])
async def list_line_groups(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["boss", "supervisor"]))
):
    # 取得所有的 LINE 群组 (Get all LINE groups)
    result = await db.execute(select(LineGroup))
    return result.scalars().all()

@router.get("/{farm_id}/zones", response_model=List[FarmZoneResponse])
async def list_farm_zones(
    farm_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 獲取農場區域列表
    result = await db.execute(select(FarmZone).where(FarmZone.farm_id == farm_id))
    return result.scalars().all()

@router.post("/{farm_id}/zones", response_model=FarmZoneResponse)
async def create_farm_zone(
    farm_id: int,
    zone_in: FarmZoneCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["boss"]))
):
    # 新增農場區域
    new_zone = FarmZone(**zone_in.model_dump())
    new_zone.farm_id = farm_id
    db.add(new_zone)
    await db.commit()
    await db.refresh(new_zone)
    return new_zone

@router.delete("/zones/{zone_id}")
async def delete_farm_zone(
    zone_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["boss"]))
):
    # 删除農場区域
    result = await db.execute(select(FarmZone).where(FarmZone.id == zone_id))
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    
    await db.delete(zone)
    await db.commit()
    return {"status": "success"}

@router.get('/{farm_id}/crops', response_model=List[CropResponse])
async def list_crops(
    farm_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Crop).where(Crop.farm_id == farm_id))
    return result.scalars().all()

@router.post('/{farm_id}/crops', response_model=CropResponse)
async def create_crop(
    farm_id: int,
    crop_in: CropCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(['boss', 'supervisor']))
):
    new_crop = Crop(**crop_in.model_dump())
    new_crop.farm_id = farm_id
    db.add(new_crop)
    await db.commit()
    await db.refresh(new_crop)
    return new_crop

@router.put('/crops/{crop_id}', response_model=CropResponse)
async def update_crop(
    crop_id: int,
    crop_in: CropUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(['boss', 'supervisor']))
):
    result = await db.execute(select(Crop).where(Crop.id == crop_id))
    crop = result.scalar_one_or_none()
    if not crop:
        raise HTTPException(status_code=404, detail='Crop not found')
        
    for key, value in crop_in.model_dump(exclude_unset=True).items():
        setattr(crop, key, value)
        
    await db.commit()
    await db.refresh(crop)
    return crop

@router.delete('/crops/{crop_id}')
async def delete_crop(
    crop_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(['boss', 'supervisor']))
):
    result = await db.execute(select(Crop).where(Crop.id == crop_id))
    crop = result.scalar_one_or_none()
    if not crop:
        raise HTTPException(status_code=404, detail='Crop not found')
    
    await db.delete(crop)
    await db.commit()
    return {'status': 'success'}

from schemas import HarvestPlanCreate, HarvestPlanResponse
@router.post('/{farm_id}/plant', response_model=HarvestPlanResponse)
async def plant_crop(
    farm_id: int,
    plant_in: HarvestPlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from models.models import HarvestPlan, Crop
    from datetime import timedelta
    
    crop_res = await db.execute(select(Crop).where(Crop.farm_id == farm_id, Crop.name == plant_in.crop_name))
    crop = crop_res.scalar_one_or_none()
    
    if not crop:
        raise HTTPException(status_code=404, detail='Crop not found. Please add it in settings first.')
        
    expected_date = plant_in.planted_date + timedelta(days=crop.grow_days)
    
    plan = HarvestPlan(
        farm_id=farm_id,
        crop_name=plant_in.crop_name,
        planted_date=plant_in.planted_date,
        expected_harvest_date=expected_date,
        area_or_zone=plant_in.area_or_zone,
        status='growing',
        notes=plant_in.notes
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan

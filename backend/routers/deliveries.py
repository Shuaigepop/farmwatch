from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List

from models.models import User, DeliveryRecord
from schemas import DeliveryRecordCreate, DeliveryRecordUpdate, DeliveryRecordResponse
from deps import get_db, get_current_user, require_role

router = APIRouter(prefix="/api/deliveries", tags=["deliveries"])

@router.get("/{farm_id}", response_model=List[DeliveryRecordResponse])
async def list_deliveries(
    farm_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "boss" and current_user.farm_id != farm_id:
        raise HTTPException(status_code=403, detail="Not authorized for this farm")
        
    query = select(DeliveryRecord).where(DeliveryRecord.farm_id == farm_id).options(selectinload(DeliveryRecord.photo)).order_by(DeliveryRecord.created_at.desc())
    result = await db.execute(query)
    records = result.scalars().all()
    
    # Map photo_url and photo_thumbnail from relationship
    res_list = []
    for r in records:
        data = r.__dict__.copy()
        if r.photo:
            data['photo_url'] = r.photo.file_path
            data['photo_thumbnail'] = r.photo.thumbnail_path
        res_list.append(data)
        
    return res_list

@router.put("/{record_id}/reconcile", response_model=DeliveryRecordResponse)
async def reconcile_delivery(
    record_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["boss"]))
):
    res = await db.execute(select(DeliveryRecord).where(DeliveryRecord.id == record_id).options(selectinload(DeliveryRecord.photo)))
    record = res.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
        
    if current_user.farm_id and current_user.farm_id != record.farm_id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    record.is_reconciled = True
    await db.commit()
    await db.refresh(record)
    
    data = record.__dict__.copy()
    if record.photo:
        data['photo_url'] = record.photo.file_path
        data['photo_thumbnail'] = record.photo.thumbnail_path
        
    return data

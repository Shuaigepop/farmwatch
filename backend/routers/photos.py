from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from database import AsyncSessionLocal
from models.models import Photo, User
from schemas import PhotoResponse
from deps import get_db, get_current_user
from services.storage_service import storage_service
import os

router = APIRouter(prefix="/api/photos", tags=["photos"])

@router.get("/", response_model=List[PhotoResponse])
async def list_photos(
    farm_id: Optional[int] = None,
    health_status: Optional[str] = None,
    target_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 獲取相片列表 (Get photo list)
    query = select(Photo)
    
    if current_user.role == "leader":
        if not current_user.farm_id:
            return []
        query = query.where(Photo.farm_id == current_user.farm_id)
    elif farm_id:
        query = query.where(Photo.farm_id == farm_id)
        
    if health_status:
        query = query.where(Photo.health_status == health_status)

    if target_date:
        from sqlalchemy import cast, Date
        from datetime import datetime
        try:
            date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()
            query = query.where(cast(Photo.captured_at, Date) == date_obj)
        except ValueError:
            pass
        
    result = await db.execute(query.order_by(Photo.captured_at.desc()))
    return result.scalars().all()

@router.get("/{photo_id}", response_model=PhotoResponse)
async def get_photo(
    photo_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 獲取單一相片 (Get single photo)
    result = await db.execute(select(Photo).where(Photo.id == photo_id))
    photo = result.scalar_one_or_none()
    
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
        
    if current_user.role == "leader" and photo.farm_id != current_user.farm_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this photo")
        
    return photo
    
@router.get("/uploads/{filename}")
async def serve_upload(filename: str):
    # 讀取上傳檔案 (Serve uploaded file)
    file_path = storage_service.get_image_path(filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    
    file_path = storage_service.get_image_path(filename, is_thumbnail=True)
    if os.path.exists(file_path):
        return FileResponse(file_path)
        
    raise HTTPException(status_code=404, detail="File not found")

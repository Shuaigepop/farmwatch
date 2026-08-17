from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
import datetime

from deps import get_db
import models.models as models
from services.line_service import LineService
from config import settings

router = APIRouter(
    prefix="/api/liff",
    tags=["liff"]
)

class LiffSubmitPayload(BaseModel):
    action: str
    farm_id: int
    line_user_id: Optional[str] = None
    
    # Delivery fields
    weight: Optional[float] = None
    baskets_out: Optional[int] = None
    baskets_in: Optional[int] = None
    
    # Supply fields
    item_id: Optional[int] = None
    quantity: Optional[float] = None
    
    # Task fields
    task_id: Optional[int] = None

@router.post("/submit")
async def submit_liff_form(payload: LiffSubmitPayload, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    line_service = LineService(settings.LINE_CHANNEL_ACCESS_TOKEN)
    
    action = payload.action
    farm_id = payload.farm_id
    line_user_id = payload.line_user_id
    
    try:
        if action == "delivery":
            record = models.DeliveryRecord(
                farm_id=farm_id,
                total_weight_kg=payload.weight or 0,
                baskets_out=payload.baskets_out or 0,
                baskets_in=payload.baskets_in or 0,
                is_reconciled=False,
                created_at=datetime.datetime.utcnow()
            )
            db.add(record)
            await db.commit()
            
        elif action == "supply":
            if not payload.item_id or payload.quantity is None:
                raise HTTPException(status_code=400, detail="Missing item_id or quantity")
                
            res = await db.execute(select(models.InventoryItem).where(
                models.InventoryItem.id == payload.item_id,
                models.InventoryItem.farm_id == farm_id
            ))
            item = res.scalars().first()
            
            if item:
                item.quantity = max(0, item.quantity - payload.quantity)
                await db.commit()
                
        elif action == "task":
            if not payload.task_id:
                raise HTTPException(status_code=400, detail="Missing task_id")
                
            res = await db.execute(select(models.Task).where(
                models.Task.id == payload.task_id,
                models.Task.farm_id == farm_id
            ))
            task = res.scalars().first()
            
            if task:
                task.status = "completed"
                task.completed_at = datetime.datetime.utcnow()
                await db.commit()
                
        else:
            raise HTTPException(status_code=400, detail="Unknown action")
            
        return {"status": "success", "message": f"{action} recorded"}
        
    except Exception as e:
        await db.rollback()
        print(f"LIFF Submit Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error")

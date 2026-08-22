from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime, date

class UserBase(BaseModel):
    username: str
    role: str
    display_name: str
    language: str = "zh"
    farm_id: Optional[int] = None

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class FarmBase(BaseModel):
    name: str
    location: Optional[str] = None
    description: Optional[str] = None
    check_time: str = "18:00"
    summary_time: str = "19:00"
    sop_time: str = "06:00"

class FarmCreate(FarmBase):
    pass

class FarmResponse(FarmBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

class FarmZoneBase(BaseModel):
    name: str
    parent_zone: Optional[str] = None
    description: Optional[str] = None

class FarmZoneCreate(FarmZoneBase):
    pass

class FarmZoneResponse(FarmZoneBase):
    id: int
    farm_id: int
    created_at: datetime
    class Config:
        from_attributes = True

class LineGroupLink(BaseModel):
    line_group_id: str
    farm_id: int
    group_name: Optional[str] = None

class MessageReply(BaseModel):
    reply_to_id: int
    content: str

class MessageSend(BaseModel):
    farm_id: int
    content: str

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    stage: Optional[str] = None
    assigned_to: Optional[int] = None
    due_date: Optional[datetime] = None
    notify_time: Optional[str] = None

class TaskCreate(TaskBase):
    farm_id: int
    zone_id: Optional[int] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    stage: Optional[str] = None
    status: Optional[str] = None
    zone_id: Optional[int] = None
    assigned_to: Optional[int] = None
    due_date: Optional[datetime] = None

class TaskResponse(TaskBase):
    id: int
    farm_id: int
    zone_id: Optional[int] = None
    status: str
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class PhotoResponse(BaseModel):
    id: int
    message_id: int
    farm_id: Optional[int]
    zone_id: Optional[int] = None
    file_path: str
    thumbnail_path: str
    ai_analysis: Optional[str]
    health_status: str
    captured_at: datetime
    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    id: int
    line_user_id: Optional[str]
    line_user_name: Optional[str]
    line_group_id: Optional[str]
    farm_id: Optional[int]
    zone_id: Optional[int] = None
    content: Optional[str]
    message_type: str
    image_url: Optional[str]
    is_reply: bool
    created_at: datetime
    class Config:
        from_attributes = True

class PasswordReset(BaseModel):
    new_password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    display_name: Optional[str] = None
    new_password: Optional[str] = None
    role: Optional[str] = None
    farm_id: Optional[int] = None

class LineGroupResponse(BaseModel):
    id: int
    line_group_id: str
    farm_id: Optional[int]
    group_name: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

class InventoryItemBase(BaseModel):
    name: str
    quantity: float
    unit: str
    item_type: str = "other"
    notes: Optional[str] = None

class InventoryItemCreate(InventoryItemBase):
    pass

class InventoryItemUpdate(BaseModel):
    name: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    item_type: Optional[str] = None
    notes: Optional[str] = None

class InventoryItemResponse(InventoryItemBase):
    id: int
    farm_id: int
    class Config:
        from_attributes = True

class DailyReportBase(BaseModel):
    report_date: str
    summary_json: str
    sent: bool = False

class DailyReportResponse(DailyReportBase):
    id: int
    farm_id: int
    sent_at: Optional[datetime] = None
    created_at: datetime
    class Config:
        from_attributes = True

class HarvestPlanBase(BaseModel):
    crop_name: str
    planted_date: date
    expected_harvest_date: date
    area_or_zone: Optional[str] = None
    status: str = "growing"
    notes: Optional[str] = None

class HarvestPlanCreate(HarvestPlanBase):
    pass

class HarvestPlanUpdate(BaseModel):
    crop_name: Optional[str] = None
    planted_date: Optional[date] = None
    expected_harvest_date: Optional[date] = None
    area_or_zone: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class HarvestPlanResponse(HarvestPlanBase):
    id: int
    farm_id: int
    created_at: datetime
    class Config:
        from_attributes = True


class CropBase(BaseModel):
    name: str
    grow_days: int = 0
    harvest_duration_days: int = 1
    is_perennial: bool = False
    notes: Optional[str] = None

class CropCreate(CropBase):
    pass

class CropUpdate(BaseModel):
    name: Optional[str] = None
    grow_days: Optional[int] = None
    harvest_duration_days: Optional[int] = None
    is_perennial: Optional[bool] = None
    notes: Optional[str] = None

class CropResponse(CropBase):
    id: int
    farm_id: int
    class Config:
        from_attributes = True

class FertilizerScheduleResponse(BaseModel):
    id: int
    farm_id: int
    month: int
    fertilizer_name: str
    quantity: float
    unit: str
    cost_per_unit: float
    class Config:
        from_attributes = True

class DeliveryRecordBase(BaseModel):
    total_weight_kg: float
    baskets_out: int = 0
    baskets_in: int = 0
    photo_id: Optional[int] = None
    is_reconciled: bool = False

class DeliveryRecordCreate(DeliveryRecordBase):
    pass


class CropBase(BaseModel):
    name: str
    grow_days: int = 0
    harvest_duration_days: int = 1
    is_perennial: bool = False
    notes: Optional[str] = None

class CropCreate(CropBase):
    pass

class CropUpdate(BaseModel):
    name: Optional[str] = None
    grow_days: Optional[int] = None
    harvest_duration_days: Optional[int] = None
    is_perennial: Optional[bool] = None
    notes: Optional[str] = None

class CropResponse(CropBase):
    id: int
    farm_id: int
    class Config:
        from_attributes = True

class FertilizerScheduleResponse(BaseModel):
    id: int
    farm_id: int
    month: int
    fertilizer_name: str
    quantity: float
    unit: str
    cost_per_unit: float
    class Config:
        from_attributes = True

class DeliveryRecordBase(BaseModel):
    total_weight_kg: float
    baskets_out: int = 0
    baskets_in: int = 0
    photo_id: Optional[int] = None
    is_reconciled: bool = False

class DeliveryRecordCreate(DeliveryRecordBase):
    pass

class DeliveryRecordUpdate(DeliveryRecordBase):
    pass

class DeliveryRecordResponse(DeliveryRecordBase):
    id: int
    farm_id: int
    uploader_id: Optional[int] = None
    created_at: datetime
    photo_url: Optional[str] = None
    photo_thumbnail: Optional[str] = None

    class Config:
        from_attributes = True

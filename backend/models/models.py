from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, Float, Date, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from database import Base

def utc_now():
    return datetime.utcnow()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String) # boss/supervisor/leader
    display_name = Column(String)
    language = Column(String, default="zh")
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=True)
    
    farm = relationship("Farm")

class Farm(Base):
    __tablename__ = "farms"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    location = Column(String)
    description = Column(Text)
    created_at = Column(DateTime, default=utc_now)

class FarmZone(Base):
    __tablename__ = "farm_zones"
    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id"))
    parent_zone = Column(String(100), nullable=True) # e.g., "A区"
    name = Column(String(100), index=True) # e.g., "A1"
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    farm = relationship("Farm")

class LineGroup(Base):
    __tablename__ = "line_groups"
    id = Column(Integer, primary_key=True, index=True)
    line_group_id = Column(String, unique=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=True)
    group_name = Column(String)
    created_at = Column(DateTime, default=utc_now)
    
    farm = relationship("Farm")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    line_user_id = Column(String, index=True)
    line_user_name = Column(String)
    line_group_id = Column(String, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=True)
    zone_id = Column(Integer, ForeignKey("farm_zones.id"), nullable=True)
    content = Column(Text)
    message_type = Column(String) # text/image
    image_url = Column(String, nullable=True)
    is_reply = Column(Boolean, default=False)
    reply_to_id = Column(Integer, ForeignKey("messages.id"), nullable=True)
    replied_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=utc_now)

    farm = relationship("Farm")
    zone = relationship("FarmZone")
    photo = relationship("Photo", back_populates="message", uselist=False)

class Photo(Base):
    __tablename__ = "photos"
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"))
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=True)
    zone_id = Column(Integer, ForeignKey("farm_zones.id"), nullable=True)
    file_path = Column(String)
    thumbnail_path = Column(String)
    ai_analysis = Column(Text, nullable=True) # JSON string
    health_status = Column(String, default="pending") # healthy/warning/critical/pending
    captured_at = Column(DateTime, default=utc_now)
    analyzed_at = Column(DateTime, nullable=True)

    message = relationship("Message", back_populates="photo")
    farm = relationship("Farm")
    zone = relationship("FarmZone")

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id"))
    zone_id = Column(Integer, ForeignKey("farm_zones.id"), nullable=True)
    title = Column(String)
    description = Column(Text)
    stage = Column(String) # seeding/fertilizing/growing/harvesting
    status = Column(String, default="pending") # pending/in_progress/completed
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    target_role = Column(String, default="worker")
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    farm = relationship("Farm")
    zone = relationship("FarmZone")
    assignee = relationship("User", foreign_keys=[assigned_to])
    verifier = relationship("User", foreign_keys=[verified_by])

class DailyReport(Base):
    __tablename__ = "daily_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    report_date = Column(Date, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id"))
    summary_json = Column(Text)
    sent = Column(Boolean, default=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    farm = relationship("Farm")

class InventoryItem(Base):
    __tablename__ = "inventory_items"
    
    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id"))
    item_type = Column(String(50)) # e.g. seed, pesticide, fertilizer
    name = Column(String(100))
    quantity = Column(Float, default=0.0)
    unit = Column(String(20)) # e.g. kg, L, bags
    notes = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    farm = relationship("Farm")

class HarvestPlan(Base):
    __tablename__ = "harvest_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id"))
    crop_name = Column(String(100))
    planted_date = Column(Date)
    expected_harvest_date = Column(Date)
    area_or_zone = Column(String(100), nullable=True)
    status = Column(String(50), default="growing") # growing, harvested, failed
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    farm = relationship("Farm")


class Crop(Base):
    __tablename__ = 'crops'
    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey('farms.id'))
    name = Column(String(100), index=True)
    grow_days = Column(Integer, default=0) # Days before first harvest
    harvest_duration_days = Column(Integer, default=1) # Days the harvest lasts
    is_perennial = Column(Boolean, default=False) # E.g., tree that lasts years
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    
    farm = relationship('Farm')

class FertilizerSchedule(Base):
    __tablename__ = 'fertilizer_schedules'
    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey('farms.id'))
    month = Column(Integer) # 1-12
    fertilizer_name = Column(String(100))
    quantity = Column(Float)
    unit = Column(String(20)) # e.g. bags, kg
    cost_per_unit = Column(Float) # e.g. 3.50
    created_at = Column(DateTime, default=utc_now)
    
    farm = relationship('Farm')

class RecurringTask(Base):
    __tablename__ = 'recurring_tasks'
    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey('farms.id'))
    zone_id = Column(Integer, ForeignKey('farm_zones.id'), nullable=True)
    title = Column(String)
    description = Column(Text)
    cron_expression = Column(String) # e.g., '0 10 * * *'
    is_active = Column(Boolean, default=True)
    target_role = Column(String, default="worker")
    created_at = Column(DateTime, default=utc_now)
    
    farm = relationship('Farm')
    zone = relationship('FarmZone')

class DeliveryRecord(Base):
    __tablename__ = 'delivery_records'
    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey('farms.id'))
    photo_id = Column(Integer, ForeignKey('photos.id'))
    total_weight_kg = Column(Float)
    baskets_out = Column(Integer, default=0)
    baskets_in = Column(Integer, default=0)
    uploader_id = Column(Integer, ForeignKey('users.id'))
    is_reconciled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)
    
    farm = relationship('Farm')
    photo = relationship('Photo')
    uploader = relationship('User')




class ProposedSchedule(Base):
    __tablename__ = 'proposed_schedules'
    
    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey('farms.id'))
    date = Column(String)  # YYYY-MM-DD
    tasks_json = Column(String)  # JSON string of proposed tasks
    status = Column(String, default='draft')  # draft, approved
    created_at = Column(DateTime, default=datetime.utcnow)
    
    farm = relationship('Farm')

class ZoneCropPlan(Base):
    __tablename__ = "zone_crop_plans"
    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id"))
    zone_id = Column(Integer, ForeignKey("farm_zones.id"))
    crop_id = Column(Integer, ForeignKey("crops.id"), nullable=True)
    crop_name = Column(String(100))
    planted_date = Column(Date, nullable=True)
    expected_harvest_date = Column(Date, nullable=True)
    harvest_end_date = Column(Date, nullable=True)
    status = Column(String(50), default="idle")
    next_crop_name = Column(String(100), nullable=True)
    last_harvest_kg = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    farm = relationship('Farm')
    zone = relationship('FarmZone')
    crop = relationship('Crop')

import asyncio
import os
import sys

# Ensure backend directory is in path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import init_db, AsyncSessionLocal
from models.models import Farm, FarmZone, Crop, FertilizerSchedule, RecurringTask

async def seed_ipoh():
    await init_db()
    async with AsyncSessionLocal() as session:
        # 1. Create Farm
        farm = Farm(name="Ipoh 菜园", location="Ipoh", description="NG LIMAU KASTURI FARM - 12 Acres")
        session.add(farm)
        await session.commit()
        await session.refresh(farm)
        
        # 2. Create Zones
        zones = [
            FarmZone(farm_id=farm.id, name="Block A", description="252 棵树, 10 行"),
            FarmZone(farm_id=farm.id, name="Block B", description="300 棵树, 10 行"),
            FarmZone(farm_id=farm.id, name="Block C", description="254 棵树, 11 行"),
            FarmZone(farm_id=farm.id, name="Block D", description="252 棵树, 10 行"),
            FarmZone(farm_id=farm.id, name="Block E", description="306 棵树, 12 行"),
            FarmZone(farm_id=farm.id, name="Block F", description="324 棵树, 12 行"),
            FarmZone(farm_id=farm.id, name="Pump House 1", description="靠近 Block A"),
            FarmZone(farm_id=farm.id, name="Pump House 2", description="靠近 Block D"),
            FarmZone(farm_id=farm.id, name="Store Room 1", description="靠近 Block A"),
            FarmZone(farm_id=farm.id, name="Hostel 1", description="主路左边 (靠近 Block C)"),
            FarmZone(farm_id=farm.id, name="Hostel 2", description="主路右边 (靠近 Block C)")
        ]
        session.add_all(zones)
        
        # 3. Create Crops
        crops = [
            Crop(farm_id=farm.id, name="Kangkong", grow_days=18, harvest_duration_days=1, is_perennial=False),
            Crop(farm_id=farm.id, name="Bayam hijau", grow_days=24, harvest_duration_days=1, is_perennial=False),
            Crop(farm_id=farm.id, name="Bayam merah", grow_days=24, harvest_duration_days=1, is_perennial=False),
            Crop(farm_id=farm.id, name="Bendi", grow_days=45, harvest_duration_days=60, is_perennial=False),
            Crop(farm_id=farm.id, name="Timun", grow_days=38, harvest_duration_days=30, is_perennial=False),
            Crop(farm_id=farm.id, name="Kacang panjang", grow_days=55, harvest_duration_days=45, is_perennial=False),
            Crop(farm_id=farm.id, name="Limau kasturi", grow_days=730, harvest_duration_days=3650, is_perennial=True)
        ]
        session.add_all(crops)
        
        # 4. Create Fertilizer Schedules
        fert_scheds = []
        for month in [1, 3, 5, 7, 9, 11]:
            fert_scheds.append(FertilizerSchedule(farm_id=farm.id, month=month, fertilizer_name="鸡粪", quantity=550, unit="包", cost_per_unit=3.50))
        for month in [2, 4, 6, 8, 10, 12]:
            fert_scheds.append(FertilizerSchedule(farm_id=farm.id, month=month, fertilizer_name="Calcium Nitrate", quantity=20, unit="包", cost_per_unit=70.0))
        for month in [4, 8, 12]:
            fert_scheds.append(FertilizerSchedule(farm_id=farm.id, month=month, fertilizer_name="Potassium Nitrate", quantity=10, unit="包", cost_per_unit=200.0))
        session.add_all(fert_scheds)
        
        # 5. Create Recurring Tasks (SOPs)
        # Saturday is cron day 5 in apscheduler if counting Mon=0.
        tasks = [
            RecurringTask(farm_id=farm.id, title="Siram air (Pump 1)", description="Block A 20min, Block B 20min, Block C 20min", cron_expression="0 10 * * *", is_active=True),
            RecurringTask(farm_id=farm.id, title="Siram air (Pump 2)", description="Block D 20min, Block E 20min, Block F 20min", cron_expression="0 10 * * *", is_active=True),
            RecurringTask(farm_id=farm.id, title="Spraying Block A, B, C", description="Spray crops in Block A -> B -> C", cron_expression="30 15 * * 5", is_active=True), 
            RecurringTask(farm_id=farm.id, title="Spraying Block D, E, F", description="Spray crops in Block D -> E -> F", cron_expression="30 15 * * 6", is_active=True)
        ]
        session.add_all(tasks)
        
        await session.commit()
        print(f"Ipoh farm (ID: {farm.id}) seed data successfully created!")

if __name__ == "__main__":
    asyncio.run(seed_ipoh())

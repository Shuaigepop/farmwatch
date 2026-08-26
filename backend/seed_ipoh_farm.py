import asyncio
from sqlalchemy import select
from sqlalchemy.sql import text
from database import AsyncSessionLocal
from models.models import Farm, FarmZone, RecurringTask, User

async def seed_ipoh_farm():
    async with AsyncSessionLocal() as session:
        # Migrate columns safely just in case
        try:
            await session.execute(text("ALTER TABLE farms ADD COLUMN IF NOT EXISTS check_time VARCHAR DEFAULT '18:00';"))
            await session.execute(text("ALTER TABLE farms ADD COLUMN IF NOT EXISTS summary_time VARCHAR DEFAULT '19:00';"))
            await session.execute(text("ALTER TABLE farms ADD COLUMN IF NOT EXISTS sop_time VARCHAR DEFAULT '06:00';"))
            await session.execute(text("ALTER TABLE recurring_tasks ADD COLUMN IF NOT EXISTS target_role VARCHAR DEFAULT 'worker';"))
            await session.commit()
        except Exception:
            pass

        # 1. Target "ipoh" Farm
        print("Targeting 'ipoh' Farm...")
        result = await session.execute(select(Farm).where(Farm.name == "ipoh"))
        farm = result.scalar_one_or_none()
        
        if not farm:
            farm = Farm(name="ipoh", location="Ipoh", description="Limau Kasturi Plantation")
            session.add(farm)
            await session.commit()
            await session.refresh(farm)
            print(f"Farm 'ipoh' created with ID: {farm.id}")
        else:
            print(f"Farm 'ipoh' already exists with ID: {farm.id}")

        # Ensure leader is assigned to ipoh
        leader_res = await session.execute(select(User).where(User.username == "leader"))
        leader = leader_res.scalar_one_or_none()
        if leader:
            leader.farm_id = farm.id
            session.add(leader)
            
        # 2. Delete all other farms and their related data to avoid FK constraints
        other_farms_res = await session.execute(select(Farm).where(Farm.name != "ipoh"))
        other_farms = other_farms_res.scalars().all()
        for of in other_farms:
            print(f"Deleting unrelated farm: {of.name}")
            # Unlink users from this farm
            await session.execute(text(f"UPDATE users SET farm_id = NULL WHERE farm_id={of.id}"))
            
            # Delete dependent records
            await session.execute(text(f"DELETE FROM zone_crop_plans WHERE farm_id={of.id}"))
            await session.execute(text(f"DELETE FROM proposed_schedules WHERE farm_id={of.id}"))
            await session.execute(text(f"DELETE FROM delivery_records WHERE farm_id={of.id}"))
            await session.execute(text(f"DELETE FROM recurring_tasks WHERE farm_id={of.id}"))
            await session.execute(text(f"DELETE FROM fertilizer_schedules WHERE farm_id={of.id}"))
            await session.execute(text(f"DELETE FROM crops WHERE farm_id={of.id}"))
            await session.execute(text(f"DELETE FROM harvest_plans WHERE farm_id={of.id}"))
            await session.execute(text(f"DELETE FROM inventory_items WHERE farm_id={of.id}"))
            await session.execute(text(f"DELETE FROM daily_reports WHERE farm_id={of.id}"))
            await session.execute(text(f"DELETE FROM tasks WHERE farm_id={of.id}"))
            await session.execute(text(f"DELETE FROM photos WHERE farm_id={of.id}"))
            await session.execute(text(f"DELETE FROM messages WHERE farm_id={of.id}"))
            await session.execute(text(f"DELETE FROM line_groups WHERE farm_id={of.id}"))
            await session.execute(text(f"DELETE FROM farm_zones WHERE farm_id={of.id}"))
            
            # Finally delete the farm
            await session.delete(of)
        
        await session.commit()
            
        # 3. Create Zones (Block A to F) for ipoh, and clean up demo ones
        zones = ["Block A", "Block B", "Block C", "Block D", "Block E", "Block F"]
        
        # Delete demo zones for ipoh (A区, B区, etc.)
        await session.execute(text(f"DELETE FROM zone_crop_plans WHERE farm_id={farm.id} AND zone_id IN (SELECT id FROM farm_zones WHERE farm_id={farm.id} AND name NOT LIKE 'Block%')"))
        await session.execute(text(f"DELETE FROM recurring_tasks WHERE farm_id={farm.id} AND title NOT LIKE '[土施肥]%' AND title NOT LIKE '[叶面喷施]%'"))
        await session.execute(text(f"DELETE FROM farm_zones WHERE farm_id={farm.id} AND name NOT LIKE 'Block%'"))
        await session.commit()
        
        # Create Crop "青金桔 (Limau Kasturi)"
        from models.models import Crop, ZoneCropPlan
        import datetime
        crop_res = await session.execute(select(Crop).where(Crop.farm_id == farm.id, Crop.name == "青金桔 (Limau Kasturi)"))
        crop = crop_res.scalar_one_or_none()
        if not crop:
            crop = Crop(farm_id=farm.id, name="青金桔 (Limau Kasturi)", grow_days=365, harvest_duration_days=1000, is_perennial=True)
            session.add(crop)
            await session.commit()
            await session.refresh(crop)
            
        today = datetime.date.today()
        
        zone_db_map = {}
        for z_name in zones:
            z_result = await session.execute(select(FarmZone).where(FarmZone.farm_id == farm.id, FarmZone.name == z_name))
            z = z_result.scalar_one_or_none()
            if not z:
                z = FarmZone(farm_id=farm.id, name=z_name)
                session.add(z)
                await session.commit()
                await session.refresh(z)
            zone_db_map[z_name] = z
            
            # Create a basic plan if none exists
            plan_res = await session.execute(select(ZoneCropPlan).where(ZoneCropPlan.zone_id == z.id))
            if not plan_res.scalar_one_or_none():
                plan = ZoneCropPlan(
                    farm_id=farm.id,
                    zone_id=z.id,
                    crop_id=crop.id,
                    crop_name=crop.name,
                    planted_date=today - datetime.timedelta(days=200),
                    expected_harvest_date=today + datetime.timedelta(days=165),
                    harvest_end_date=today + datetime.timedelta(days=1000),
                    status="growing",
                    notes="Limau Kasturi Block"
                )
                session.add(plan)
        await session.commit()
            
        # Clear existing recurring tasks for this farm to avoid duplicates
        existing_rt = await session.execute(select(RecurringTask).where(RecurringTask.farm_id == farm.id))
        for rt in existing_rt.scalars().all():
            await session.delete(rt)
        await session.commit()
            
        # 4. Create Recurring Tasks
        print("Creating Recurring Tasks for 'ipoh'...")
        
        tasks_to_create = [
            RecurringTask(farm_id=farm.id, title="[土施肥] 鸡粪 550包", description="全园施放鸡粪，共 550 包。管理原则：土施负责长期营养供应。", cron_expression="0 8 1 1,3,5,7,9,11 *", target_role="worker"),
            RecurringTask(farm_id=farm.id, title="[土施肥] Calcium Nitrate 25kg × 20包", description="全园施放 Calcium Nitrate 25kg × 20包。", cron_expression="0 8 1 2,6,10 *", target_role="worker"),
            RecurringTask(farm_id=farm.id, title="[土施肥] Calcium Nitrate(20包) + Potassium Nitrate(10包)", description="全园施放 Calcium Nitrate 25kg × 20包 以及 Potassium Nitrate 25kg × 10包。", cron_expression="0 8 1 4,8,12 *", target_role="worker"),
            RecurringTask(farm_id=farm.id, title="[叶面喷施] 周六 Block A→B→C (800L)", description="喷药前先浇水，待叶面基本干燥后开始喷药。\n配方(每20L)：DG 40ml, JS 30ml(雨季或菌害严重40ml)。\n* 第1周加强配方：加入 C-M Monthly Boost 70ml\n* 第2~5周标准配方：加入 C-W Weekly 70ml", cron_expression="30 15 * * 6", target_role="worker"),
            RecurringTask(farm_id=farm.id, title="[叶面喷施] 周日 Block D→E→F (800L)", description="喷药前先浇水，待叶面基本干燥后开始喷药。\n配方(每20L)：DG 40ml, JS 30ml(雨季或菌害严重40ml)。\n* 第1周加强配方：加入 C-M Monthly Boost 70ml\n* 第2~5周标准配方：加入 C-W Weekly 70ml", cron_expression="30 15 * * 0", target_role="worker")
        ]
        
        session.add_all(tasks_to_create)
        await session.commit()
        print("Data seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed_ipoh_farm())

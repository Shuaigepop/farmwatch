import asyncio
from sqlalchemy import select, and_
from database import AsyncSessionLocal
from models.models import Farm, FarmZone, RecurringTask

async def seed_ipoh_farm():
    async with AsyncSessionLocal() as session:
        from sqlalchemy import text
        try:
            await session.execute(text("ALTER TABLE farms ADD COLUMN IF NOT EXISTS check_time VARCHAR DEFAULT '18:00';"))
            await session.execute(text("ALTER TABLE farms ADD COLUMN IF NOT EXISTS summary_time VARCHAR DEFAULT '19:00';"))
            await session.execute(text("ALTER TABLE farms ADD COLUMN IF NOT EXISTS sop_time VARCHAR DEFAULT '06:00';"))
            await session.execute(text("ALTER TABLE recurring_tasks ADD COLUMN IF NOT EXISTS target_role VARCHAR DEFAULT 'worker';"))
            await session.commit()
        except Exception:
            pass

        # 1. Create Farm
        print("Creating Farm...")
        result = await session.execute(select(Farm).where(Farm.name == "NG Limau Kasturi Farm"))
        farm = result.scalar_one_or_none()
        
        if not farm:
            farm = Farm(name="NG Limau Kasturi Farm", location="Ipoh", description="Limau Kasturi Plantation")
            session.add(farm)
            await session.commit()
            await session.refresh(farm)
            print(f"Farm created with ID: {farm.id}")
        else:
            print(f"Farm already exists with ID: {farm.id}")
            
        # 2. Create Zones (Block A to F)
        zones = ["Block A", "Block B", "Block C", "Block D", "Block E", "Block F"]
        zone_ids = {}
        for z_name in zones:
            z_result = await session.execute(select(FarmZone).where(FarmZone.farm_id == farm.id, FarmZone.name == z_name))
            z = z_result.scalar_one_or_none()
            if not z:
                z = FarmZone(farm_id=farm.id, name=z_name)
                session.add(z)
                await session.commit()
                await session.refresh(z)
            zone_ids[z_name] = z.id
            
        # Clear existing recurring tasks for this farm to avoid duplicates
        existing_rt = await session.execute(select(RecurringTask).where(RecurringTask.farm_id == farm.id))
        for rt in existing_rt.scalars().all():
            await session.delete(rt)
        await session.commit()
            
        # 3. Create Recurring Tasks
        print("Creating Recurring Tasks...")
        
        tasks_to_create = [
            # 土施肥 (Soil Fertilizer)
            RecurringTask(
                farm_id=farm.id,
                title="[土施肥] 鸡粪 550包",
                description="全园施放鸡粪，共 550 包。管理原则：土施负责长期营养供应。",
                cron_expression="0 8 1 1,3,5,7,9,11 *", # 1st day of odd months at 08:00
                target_role="worker"
            ),
            RecurringTask(
                farm_id=farm.id,
                title="[土施肥] Calcium Nitrate 25kg × 20包",
                description="全园施放 Calcium Nitrate 25kg × 20包。",
                cron_expression="0 8 1 2,6,10 *", # 1st day of Feb, Jun, Oct
                target_role="worker"
            ),
            RecurringTask(
                farm_id=farm.id,
                title="[土施肥] Calcium Nitrate(20包) + Potassium Nitrate(10包)",
                description="全园施放 Calcium Nitrate 25kg × 20包 以及 Potassium Nitrate 25kg × 10包。",
                cron_expression="0 8 1 4,8,12 *", # 1st day of Apr, Aug, Dec
                target_role="worker"
            ),
            
            # 叶面喷施 (Foliar Spray) - Saturday
            RecurringTask(
                farm_id=farm.id,
                title="[叶面喷施] 周六 Block A→B→C (800L)",
                description="喷药前先浇水，待叶面基本干燥后开始喷药。\n配方(每20L)：DG 40ml, JS 30ml(雨季或菌害严重40ml)。\n* 第1周加强配方：加入 C-M Monthly Boost 70ml\n* 第2~5周标准配方：加入 C-W Weekly 70ml",
                cron_expression="30 15 * * 6", # Sat 15:30
                target_role="worker"
            ),
            
            # 叶面喷施 (Foliar Spray) - Sunday
            RecurringTask(
                farm_id=farm.id,
                title="[叶面喷施] 周日 Block D→E→F (800L)",
                description="喷药前先浇水，待叶面基本干燥后开始喷药。\n配方(每20L)：DG 40ml, JS 30ml(雨季或菌害严重40ml)。\n* 第1周加强配方：加入 C-M Monthly Boost 70ml\n* 第2~5周标准配方：加入 C-W Weekly 70ml",
                cron_expression="30 15 * * 0", # Sun 15:30
                target_role="worker"
            )
        ]
        
        session.add_all(tasks_to_create)
        await session.commit()
        print("Data seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed_ipoh_farm())

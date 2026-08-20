import asyncio
import os
import sys
from datetime import datetime, timedelta, date
from sqlalchemy import select, delete

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from database import init_db, AsyncSessionLocal
from models.models import Farm, FarmZone, Crop, FertilizerSchedule, RecurringTask, ZoneCropPlan, InventoryItem

async def seed_farm_demo(session, farm_id: int):
    # 1. Ensure Crops Exist
    crop_list = [
        {"name": "秋葵 (Bendi)", "grow_days": 45, "harvest_duration_days": 60, "is_perennial": False},
        {"name": "空心菜 (Kangkong)", "grow_days": 25, "harvest_duration_days": 10, "is_perennial": False},
        {"name": "长豆 (Kacang Panjang)", "grow_days": 50, "harvest_duration_days": 30, "is_perennial": False},
        {"name": "黄瓜 (Timun)", "grow_days": 38, "harvest_duration_days": 25, "is_perennial": False},
        {"name": "青金桔 (Limau Kasturi)", "grow_days": 365, "harvest_duration_days": 1000, "is_perennial": True},
    ]
    
    crop_db_map = {}
    for c in crop_list:
        c_res = await session.execute(select(Crop).where(Crop.farm_id == farm_id, Crop.name == c["name"]))
        existing_crop = c_res.scalar_one_or_none()
        if not existing_crop:
            new_c = Crop(
                farm_id=farm_id,
                name=c["name"],
                grow_days=c["grow_days"],
                harvest_duration_days=c["harvest_duration_days"],
                is_perennial=c["is_perennial"]
            )
            session.add(new_c)
            await session.flush()
            crop_db_map[c["name"]] = new_c
        else:
            crop_db_map[c["name"]] = existing_crop

    # 2. Ensure Zones Exist
    zone_names = [
        ("A区", "A1区 - 秋葵田"),
        ("A区", "A2区 - 叶菜区"),
        ("B区", "B1区 - 豆类高架"),
        ("B区", "B2区 - 翻土整顿区"),
        ("C区", "C1区 - 金桔果园"),
    ]
    
    zone_db_map = {}
    for parent, name in zone_names:
        z_res = await session.execute(select(FarmZone).where(FarmZone.farm_id == farm_id, FarmZone.name == name))
        existing_z = z_res.scalar_one_or_none()
        if not existing_z:
            new_z = FarmZone(farm_id=farm_id, parent_zone=parent, name=name)
            session.add(new_z)
            await session.flush()
            zone_db_map[name] = new_z
        else:
            zone_db_map[name] = existing_z

    await session.commit()

    # 3. Create ZoneCropPlans (The Farm Planning Map!)
    today = date.today()
    
    plans = [
        # A1: 秋葵 - 种植了 43 天 -> 还有 2 天采收！(⚠️ 预警)
        ZoneCropPlan(
            farm_id=farm_id,
            zone_id=zone_db_map["A1区 - 秋葵田"].id,
            crop_id=crop_db_map["秋葵 (Bendi)"].id,
            crop_name="秋葵 (Bendi)",
            planted_date=today - timedelta(days=43),
            expected_harvest_date=today + timedelta(days=2),
            harvest_end_date=today + timedelta(days=62),
            status="growing",
            next_crop_name="空心菜",
            last_harvest_kg=350.0,
            notes="生长良好，预估2天后开始第一批采收"
        ),
        # A2: 空心菜 - 种植了 25 天 -> 今天采收！
        ZoneCropPlan(
            farm_id=farm_id,
            zone_id=zone_db_map["A2区 - 叶菜区"].id,
            crop_id=crop_db_map["空心菜 (Kangkong)"].id,
            crop_name="空心菜 (Kangkong)",
            planted_date=today - timedelta(days=25),
            expected_harvest_date=today,
            harvest_end_date=today + timedelta(days=5),
            status="growing",
            next_crop_name="黄瓜",
            last_harvest_kg=120.0,
            notes="今日需安排采收并打包"
        ),
        # B1: 长豆 - 采收中
        ZoneCropPlan(
            farm_id=farm_id,
            zone_id=zone_db_map["B1区 - 豆类高架"].id,
            crop_id=crop_db_map["长豆 (Kacang Panjang)"].id,
            crop_name="长豆 (Kacang Panjang)",
            planted_date=today - timedelta(days=55),
            expected_harvest_date=today - timedelta(days=5),
            harvest_end_date=today + timedelta(days=25),
            status="harvesting",
            next_crop_name="秋葵",
            last_harvest_kg=280.0,
            notes="每日上午采收，注意防治蚜虫"
        ),
        # B2: 准备翻土
        ZoneCropPlan(
            farm_id=farm_id,
            zone_id=zone_db_map["B2区 - 翻土整顿区"].id,
            crop_id=None,
            crop_name="无 (上一轮: 黄瓜)",
            planted_date=None,
            expected_harvest_date=None,
            harvest_end_date=None,
            status="preparing",
            next_crop_name="黄瓜 (Timun)",
            last_harvest_kg=450.0,
            notes="上一轮已清理完残株，等待翻土施底肥"
        ),
        # C1: 金桔 - 果树长期生长
        ZoneCropPlan(
            farm_id=farm_id,
            zone_id=zone_db_map["C1区 - 金桔果园"].id,
            crop_id=crop_db_map["青金桔 (Limau Kasturi)"].id,
            crop_name="青金桔 (Limau Kasturi)",
            planted_date=today - timedelta(days=200),
            expected_harvest_date=today + timedelta(days=165),
            harvest_end_date=today + timedelta(days=1000),
            status="growing",
            next_crop_name="多年生果树",
            last_harvest_kg=890.0,
            notes="定期剪枝与注意柑橘黄龙病预防"
        ),
    ]
    session.add_all(plans)

    # 4. Create SOPs (Recurring Tasks)
    sops = [
        RecurringTask(
            farm_id=farm_id,
            zone_id=zone_db_map["A1区 - 秋葵田"].id,
            title="A区/B区 早间定时自动灌溉检查",
            description="检查 Pump 1 压力与滴灌管线，开启灌溉 30 分钟",
            cron_expression="0 8 * * *",
            is_active=True
        ),
        RecurringTask(
            farm_id=farm_id,
            zone_id=None,
            title="全农场常规病虫害巡检与例行记录",
            description="重点观察叶背虫卵与土壤湿度，拍照上传 LINE",
            cron_expression="0 9 * * *",
            is_active=True
        ),
        RecurringTask(
            farm_id=farm_id,
            zone_id=zone_db_map["C1区 - 金桔果园"].id,
            title="周四有机防虫药剂喷洒 (金桔区)",
            description="调配苦楝油与木醋液进行全面叶面喷洒",
            cron_expression="0 15 * * 4",
            is_active=True
        )
    ]
    session.add_all(sops)

    # 5. Create Fertilizer Schedule for current month
    current_month = today.month
    fert_scheds = [
        FertilizerSchedule(
            farm_id=farm_id,
            month=current_month,
            fertilizer_name="有机鸡粪肥 (发酵颗粒)",
            quantity=20,
            unit="包",
            cost_per_unit=12.0
        ),
        FertilizerSchedule(
            farm_id=farm_id,
            month=current_month,
            fertilizer_name="高钾水溶肥 15-5-30",
            quantity=3,
            unit="桶",
            cost_per_unit=85.0
        )
    ]
    session.add_all(fert_scheds)

    # 6. Create Low Inventory Items for Alerts
    inventories = [
        InventoryItem(farm_id=farm_id, item_type="tools", name="采收塑料篮 (Baskets)", quantity=12.0, unit="个", notes="低库存！采收期需至少50个"),
        InventoryItem(farm_id=farm_id, item_type="pesticide", name="苦楝油防虫剂", quantity=2.5, unit="L", notes="低库存！预估本周用完"),
        InventoryItem(farm_id=farm_id, item_type="fertilizer", name="有机鸡粪肥", quantity=150.0, unit="包", notes="库存充足")
    ]
    session.add_all(inventories)

    await session.commit()
    print(f"Demo seed data for Farm ID {farm_id} created successfully!")

async def auto_seed_all_farms(session):
    # Check all farms
    farms_res = await session.execute(select(Farm))
    farms = farms_res.scalars().all()
    for farm in farms:
        # Check if this farm has zone_crop_plans
        plans_res = await session.execute(select(ZoneCropPlan).where(ZoneCropPlan.farm_id == farm.id))
        existing_plans = plans_res.scalars().all()
        if not existing_plans:
            print(f"Auto seeding farm ID {farm.id} ({farm.name})...")
            await seed_farm_demo(session, farm.id)

async def main():
    await init_db()
    async with AsyncSessionLocal() as session:
        await auto_seed_all_farms(session)

if __name__ == "__main__":
    asyncio.run(main())

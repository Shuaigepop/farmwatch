import json
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import models
from services.ai_service import ai_service
from google.genai import types

async def generate_daily_schedule(farm_id: int, db: AsyncSession):
    # 1. Fetch recent photos with issues
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    res = await db.execute(select(models.Photo).where(
        models.Photo.farm_id == farm_id,
        models.Photo.captured_at >= yesterday,
        models.Photo.health_status.in_(["warning", "critical"])
    ))
    bad_photos = res.scalars().all()
    
    photo_summaries = []
    for p in bad_photos:
        photo_summaries.append(f"Zone {p.zone_id}: {p.ai_analysis}")
    
    # Agent 1: Disease Expert
    prompt1 = f"""
    【植物病理专家 AI】
    最近24小时有以下警告照片分析：
    {photo_summaries}
    请根据这些状况提供建议，建议农场今天应该执行哪些任务来处理这些病害问题？
    """
    resp1 = ai_service.client.models.generate_content(
        model='gemini-3.5-flash',
        contents=[prompt1]
    )
    agent1_suggestion = resp1.text

    # 2. Fetch inventory
    inv_res = await db.execute(select(models.InventoryItem).where(models.InventoryItem.farm_id == farm_id))
    inventory = inv_res.scalars().all()
    inv_data = [{"name": i.name, "quantity": i.quantity, "unit": i.unit} for i in inventory]
    
    # Agent 2: Inventory Expert
    prompt2 = f"""
    【库存管理专家 AI】
    目前库存状况：
    {inv_data}
    请分析是否有极低库存的项目，并建议今天是否需要盘点或采购任务？
    """
    resp2 = ai_service.client.models.generate_content(
        model='gemini-3.5-flash',
        contents=[prompt2]
    )
    agent2_suggestion = resp2.text

    # 3. Fetch pending tasks
    tasks_res = await db.execute(select(models.Task).where(
        models.Task.farm_id == farm_id,
        models.Task.status == "pending"
    ))
    pending_tasks = tasks_res.scalars().all()
    task_data = [{"title": t.title, "description": t.description, "zone_id": t.zone_id} for t in pending_tasks]

    # Agent 3: Coordinator
    prompt3 = f"""
    【农场大管家 AI】
    请根据以下信息，安排今天的任务行程。
    疾病专家建议：{agent1_suggestion}
    库存专家建议：{agent2_suggestion}
    目前的待办任务：{task_data}
    
    请输出一个 JSON 阵列（Array），包含今天要执行的任务列表。
    每个任务必须是一个 JSON 对象，包含以下栏位：
    - "title": 任务标题
    - "zone_id": 区域ID（如果有对应，可填整数；若无特定区域可填 null）
    - "description": 任务详细说明
    只回传纯 JSON，不要包含 ```json 标签。
    """
    
    resp3 = ai_service.client.models.generate_content(
        model='gemini-3.5-flash',
        contents=[prompt3],
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )
    
    tasks_json = resp3.text
    
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Save to ProposedSchedule
    exist_res = await db.execute(select(models.ProposedSchedule).where(
        models.ProposedSchedule.farm_id == farm_id,
        models.ProposedSchedule.date == today_str
    ))
    existing = exist_res.scalar_one_or_none()
    
    if existing:
        existing.tasks_json = tasks_json
        existing.status = "draft"
    else:
        new_schedule = models.ProposedSchedule(
            farm_id=farm_id,
            date=today_str,
            tasks_json=tasks_json,
            status="draft"
        )
        db.add(new_schedule)
    
    await db.commit()
    return json.loads(tasks_json)

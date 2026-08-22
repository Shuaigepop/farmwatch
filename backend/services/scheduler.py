from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, date, timedelta, timezone
import json
import asyncio

from database import AsyncSessionLocal
from models.models import User, Farm, Message, Task, Photo, DailyReport, LineGroup, InventoryItem, RecurringTask, HarvestPlan, Crop, FarmZone
from services.ai_service import ai_service
from services.line_service import line_service
from config import settings

scheduler = AsyncIOScheduler()

def utc_now():
    return datetime.now(timezone.utc)

async def generate_and_send_daily_reports():
    print(f"[{datetime.now()}] Generating daily reports...")
    try:
        async with AsyncSessionLocal() as session:
            farms_result = await session.execute(select(Farm))
            farms = farms_result.scalars().all()
            
            groups_result = await session.execute(select(LineGroup.line_group_id))
            all_groups = groups_result.scalars().all()
            
            yesterday = datetime.now(timezone.utc) - timedelta(days=1)
            
            for farm in farms:
                msg_res = await session.execute(select(Message).where(and_(Message.farm_id == farm.id, Message.created_at >= yesterday)))
                messages = [{"type": m.message_type, "content": m.content, "user": m.line_user_name, "time": str(m.created_at)} for m in msg_res.scalars().all()]
                
                task_res = await session.execute(select(Task).where(and_(Task.farm_id == farm.id, Task.status != "completed")))
                tasks = [{"title": t.title, "stage": t.stage, "status": t.status} for t in task_res.scalars().all()]
                
                inv_res = await session.execute(select(InventoryItem).where(InventoryItem.farm_id == farm.id))
                inventory = [{"name": i.name, "quantity": i.quantity, "unit": i.unit} for i in inv_res.scalars().all()]
                
                photo_res = await session.execute(select(Photo).where(and_(Photo.farm_id == farm.id, Photo.captured_at >= yesterday)))
                photos = [{"status": p.health_status, "ai_notes": p.ai_analysis} for p in photo_res.scalars().all()]
                
                if tasks or photos or inventory:
                    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                    analyst_report = await ai_service.analyze_data(inventory, tasks)
                    print(f"[{farm.name}] Analyst Report generated.")
                    
                    summary_text = await ai_service.generate_daily_summary(date_str, analyst_report, tasks, photos)
                    print(f"[{farm.name}] Manager Summary generated.")
                    
                    report = DailyReport(
                        report_date=datetime.now().strftime("%Y-%m-%d"),
                        farm_id=farm.id,
                        summary_json=json.dumps({"text": summary_text}, ensure_ascii=False),
                        sent=True,
                        sent_at=datetime.now(timezone.utc)
                    )
                    session.add(report)
                    await session.commit()
                    
                    for group_id in all_groups:
                        line_service.send_text_message(group_id, f"📊 【FarmWatch 大管家日报 - {farm.name}】\n\n{summary_text}")
    except Exception as e:
        print(f"Error in daily report job: {e}")


async def create_task_from_template(recurring_task_id: int):
    """Callback for APScheduler to generate a Task when the cron triggers."""
    try:
        async with AsyncSessionLocal() as session:
            rt = await session.get(RecurringTask, recurring_task_id)
            if not rt or not rt.is_active:
                return
                
            new_task = Task(
                farm_id=rt.farm_id,
                zone_id=rt.zone_id,
                title=rt.title,
                description=rt.description,
                stage="growing", # Or maybe something general
                status="pending",
                due_date=utc_now() + timedelta(hours=24)
            )
            session.add(new_task)
            await session.commit()
            print(f"Generated task from recurring rule: {rt.title}")
    except Exception as e:
        print(f"Error creating task from template: {e}")

async def sync_recurring_jobs():
    """Load recurring tasks from DB and add them to APScheduler."""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(RecurringTask).where(RecurringTask.is_active == True))
            r_tasks = result.scalars().all()
            
            # Clear existing dynamically added jobs to refresh
            for job in scheduler.get_jobs():
                if job.id.startswith('rt_'):
                    scheduler.remove_job(job.id)
                    
            for rt in r_tasks:
                parts = rt.cron_expression.split()
                if len(parts) == 5:
                    minute, hour, day, month, day_of_week = parts
                    scheduler.add_job(
                        create_task_from_template,
                        CronTrigger(minute=minute, hour=hour, day=day, month=month, day_of_week=day_of_week),
                        args=[rt.id],
                        id=f'rt_{rt.id}',
                        replace_existing=True
                    )
        print(f"Loaded {len(r_tasks)} recurring tasks into scheduler.")
    except Exception as e:
        print(f"Error syncing recurring jobs: {e}")

async def generate_harvest_tasks():
    """Daily check for crops that need harvesting today."""
    today = date.today()
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(HarvestPlan).where(HarvestPlan.status == "growing"))
            plans = result.scalars().all()
            
            for plan in plans:
                crop_result = await session.execute(select(Crop).where(
                    Crop.farm_id == plan.farm_id, 
                    Crop.name == plan.crop_name
                ))
                crop = crop_result.scalars().first()
                
                harvest_duration = crop.harvest_duration_days if crop else 1
                harvest_end_date = plan.expected_harvest_date + timedelta(days=harvest_duration)
                
                # Check if today is harvest day
                if plan.expected_harvest_date <= today <= harvest_end_date:
                    new_task = Task(
                        farm_id=plan.farm_id,
                        title=f"采收: {plan.crop_name}",
                        description=f"种植日期: {plan.planted_date}. 预计结束采收: {harvest_end_date}",
                        stage="harvesting",
                        status="pending",
                        due_date=utc_now() + timedelta(hours=24)
                    )
                    session.add(new_task)
                    
                # Mark as completed if harvest duration is over and it's not perennial
                elif today > harvest_end_date and crop and not crop.is_perennial:
                    plan.status = "harvested"
                    
            await session.commit()
            print("Completed daily harvest task generation.")
    except Exception as e:
        print(f"Error generating harvest tasks: {e}")


async def schedule_watering_task():
    print(f"[{datetime.now()}] Running 11AM watering task...")
    try:
        async with AsyncSessionLocal() as session:
            groups_result = await session.execute(select(LineGroup.line_group_id))
            all_groups = groups_result.scalars().all()
            for group_id in all_groups:
                reply = "🚰 浇水时间到了！请为每个 Lot 浇水 20 分钟。\n🚰 Watering time! Please water each lot for 20 mins.\n🚰 Masa untuk menyiram! Sila siram setiap lot selama 20 minit.\n🚰 ရေလောင်းရန်အချိန်ရောက်ပါပြီ! တစ်ကွက်လျှင် မိနစ် ၂၀ ရေလောင်းပါ။"
                line_service.send_text_message(group_id, reply)
    except Exception as e:
        print(f"Error in schedule_watering_task: {e}")

async def check_missing_work_by_farms(farms_to_check):
    print(f"[{datetime.now()}] Running missing work check for {len(farms_to_check)} farms...")
    try:
        async with AsyncSessionLocal() as session:
            farms_result = await session.execute(select(Farm).where(Farm.id.in_([f.id for f in farms_to_check])))
            farms = farms_result.scalars().all()
            groups_result = await session.execute(select(LineGroup))
            all_groups = groups_result.scalars().all()
            
            today = date.today()
            is_sunday = today.weekday() == 6
            
            for farm in farms:
                farm_groups = [g.line_group_id for g in all_groups if g.farm_id == farm.id]
                if not farm_groups:
                    continue
                
                # Check uncompleted tasks
                task_res = await session.execute(select(Task).where(and_(Task.farm_id == farm.id, Task.status != "completed")))
                uncompleted = task_res.scalars().all()
                if uncompleted:
                    task_names = ", ".join([t.title for t in uncompleted])
                    msg = f"⚠️ 以下工作还没完成 / Tasks not finished / Tugas belum selesai:\n{task_names}\n请问是什么原因？(Why? / Mengapa?)"
                    for g in farm_groups:
                        line_service.send_text_message(g, msg)
                
                # Check delivery
                if not is_sunday:
                    from models.models import DeliveryRecord
                    del_res = await session.execute(select(DeliveryRecord).where(and_(DeliveryRecord.farm_id == farm.id, DeliveryRecord.created_at >= datetime.combine(today, datetime.min.time()))))
                    deliveries = del_res.scalars().all()
                    if not deliveries:
                        msg = "⚠️ 今天没有收到出货单！是因为下雨、没熟果还是其他原因？\n⚠️ No delivery record today! Is it raining or no ripe fruits? Please explain.\n⚠️ Tiada rekod penghantaran hari ini! Hujan atau tiada buah masak? Sila jelaskan."
                        for g in farm_groups:
                            line_service.send_text_message(g, msg)
    except Exception as e:
        print(f"Error in check_missing_work_6pm: {e}")

async def generate_evening_summary_by_farms(farms_to_check):
    print(f"[{datetime.now()}] Running summary and prep for {len(farms_to_check)} farms...")
    try:
        async with AsyncSessionLocal() as session:
            farms_result = await session.execute(select(Farm).where(Farm.id.in_([f.id for f in farms_to_check])))
            farms = farms_result.scalars().all()
            groups_result = await session.execute(select(LineGroup))
            all_groups = groups_result.scalars().all()
            
            yesterday = datetime.now(timezone.utc) - timedelta(days=1)
            today_6pm = datetime.combine(date.today(), datetime.min.time().replace(hour=18))
            
            for farm in farms:
                farm_groups = [g.line_group_id for g in all_groups if g.farm_id == farm.id]
                
                # Get afternoon chats (reasons)
                msg_res = await session.execute(select(Message).where(and_(Message.farm_id == farm.id, Message.created_at >= today_6pm)))
                chats = [m.content for m in msg_res.scalars().all() if m.message_type == "text"]
                
                # Get tasks
                task_res = await session.execute(select(Task).where(Task.farm_id == farm.id))
                all_tasks = task_res.scalars().all()
                completed = [t.title for t in all_tasks if t.status == "completed"]
                pending = [t.title for t in all_tasks if t.status != "completed"]
                
                # Generate AI summary
                summary_prompt = f"Write a bilingual (Chinese/English) summary of today's work for the boss. Completed: {completed}. Pending: {pending}. Worker reasons for pending/no harvest (if any): {chats}. Keep it professional but brief."
                try:
                    ai_summary = await ai_service.generate_generic_content(summary_prompt)
                except Exception as api_err:
                    print(f"AI API failed: {api_err}")
                    ai_summary = f"系统自动摘要 (AI 摘要服务暂时无回应)\n完成任务: {len(completed)}\n未完成任务: {len(pending)}"
                
                # Boss Summary Message
                boss_msg = f"📊 【FarmWatch 今日总结 - {farm.name}】\n\n{ai_summary}"
                
                # Create tomorrow's routine per zone
                zones_res = await session.execute(select(FarmZone).where(FarmZone.farm_id == farm.id))
                farm_zones = zones_res.scalars().all()
                new_tasks = []
                for z in farm_zones:
                    t1 = Task(farm_id=farm.id, zone_id=z.id, title=f"⏰ 11:00 AM - 🚰 浇水 20m (Water / Siram / ရေလောင်း) - {z.name}", status="pending", due_date=utc_now() + timedelta(days=1))
                    t2 = Task(farm_id=farm.id, zone_id=z.id, title=f"⏰ 08:00 AM - 🔍 巡视采收 (Inspect / Periksa / စစ်ဆေးမည်) - {z.name}", status="pending", due_date=utc_now() + timedelta(days=1))
                    session.add(t1)
                    session.add(t2)
                    new_tasks.extend([t1.title, t2.title])
                await session.commit()
                pending.extend(new_tasks)
                
                # Tomorrow tasks prep
                worker_msg = f"📋 【明日工作准备 / Tomorrow's Tasks / Tugas Esok】\n"
                if pending:
                    worker_msg += "\n".join([f"- {p}" for p in pending])
                else:
                    worker_msg += "🎉 没有任何待办事项！ (All clear! / Semua selesai!)"
                
                if farm_groups:
                    for g in farm_groups:
                        line_service.send_text_message(g, boss_msg)
                        line_service.send_text_message(g, worker_msg)
    except Exception as e:
        print(f"Error in generate_evening_summary_7pm: {e}")

async def create_weekly_health_check_tasks():
    print(f"[{datetime.now()}] Running Monday health check tasks generation...")
    try:
        async with AsyncSessionLocal() as session:
            farms_result = await session.execute(select(FarmZone))
            zones = farms_result.scalars().all()
            for zone in zones:
                # Wide photo
                session.add(Task(farm_id=zone.farm_id, zone_id=zone.id, title=f"📸 拍全景照 (Wide Photo) - {zone.name}", description="", status="pending", due_date=utc_now() + timedelta(days=1)))
                # Close photo
                session.add(Task(farm_id=zone.farm_id, zone_id=zone.id, title=f"📸 拍近照 (Close Photo) - {zone.name}", description="", status="pending", due_date=utc_now() + timedelta(days=1)))
                # Video
                session.add(Task(farm_id=zone.farm_id, zone_id=zone.id, title=f"🎥 拍10秒影片 (10s Video) - {zone.name}", description="", status="pending", due_date=utc_now() + timedelta(days=1)))
            await session.commit()
    except Exception as e:
        print(f"Error in create_weekly_health_check_tasks: {e}")

async def dispatch_sops(farm, session):
    try:
        groups_result = await session.execute(select(LineGroup.line_group_id).where(LineGroup.farm_id == farm.id))
        farm_groups = groups_result.scalars().all()
        
        # Get active recurring tasks for this farm
        result = await session.execute(select(RecurringTask).where(and_(RecurringTask.farm_id == farm.id, RecurringTask.is_active == True)))
        r_tasks = result.scalars().all()
        
        if not r_tasks:
            return
            
        generated_titles = []
        for rt in r_tasks:
            new_task = Task(
                farm_id=rt.farm_id,
                zone_id=rt.zone_id,
                title=rt.title,
                description=rt.description,
                stage="growing",
                status="pending",
                target_role=rt.target_role,
                due_date=utc_now() + timedelta(hours=24)
            )
            session.add(new_task)
            generated_titles.append(rt.title)
            
        await session.commit()
        print(f"[{farm.name}] Dispatched {len(r_tasks)} SOP tasks.")
        
        # Notify LINE group
        if farm_groups and generated_titles:
            msg = f"🌅 【{farm.name} - 每日例行工作已派发】\n\n" + "\n".join([f"- {t}" for t in generated_titles])
            for g in farm_groups:
                line_service.send_text_message(g, msg)
                
    except Exception as e:
        print(f"Error in dispatch_sops for {farm.name}: {e}")

async def check_adhoc_notifications(farm, session, now_str):
    try:
        groups_result = await session.execute(select(LineGroup.line_group_id).where(LineGroup.farm_id == farm.id))
        farm_groups = groups_result.scalars().all()
        if not farm_groups:
            return
            
        # Get pending tasks that should notify now
        result = await session.execute(select(Task).where(and_(Task.farm_id == farm.id, Task.status == "pending", Task.notify_time == now_str)))
        tasks = result.scalars().all()
        
        for task in tasks:
            assignee_str = f" @ {task.assignee.display_name}" if task.assignee else " (全体员工/All)"
            msg = f"🔔 【临时任务提醒 / Task Reminder】\n\n📝 任务: {task.title}\n👤 指派给: {assignee_str}\n\n请尽快处理！(Please handle ASAP!)"
            for g in farm_groups:
                line_service.send_text_message(g, msg)
                
            # Clear notify_time so it doesn't trigger again
            task.notify_time = None
            
        if tasks:
            await session.commit()
            
    except Exception as e:
        print(f"Error in check_adhoc_notifications for {farm.name}: {e}")

async def heartbeat_check():
    """Runs every minute to trigger farm-specific tasks based on their custom times."""
    now_str = datetime.now().strftime("%H:%M")
    try:
        async with AsyncSessionLocal() as session:
            farms_result = await session.execute(select(Farm))
            farms = farms_result.scalars().all()
            
            farms_for_check = []
            farms_for_summary = []
            
            for farm in farms:
                # Default fallback if empty
                check_t = farm.check_time or "18:00"
                summary_t = farm.summary_time or "19:00"
                sop_t = farm.sop_time or "06:00"
                
                if check_t == now_str:
                    farms_for_check.append(farm)
                if summary_t == now_str:
                    farms_for_summary.append(farm)
                if sop_t == now_str:
                    await dispatch_sops(farm, session)
                    
                await check_adhoc_notifications(farm, session, now_str)
            
            if farms_for_check:
                await check_missing_work_by_farms(farms_for_check)
            if farms_for_summary:
                await generate_evening_summary_by_farms(farms_for_summary)
                
    except Exception as e:
        print(f"Error in heartbeat_check: {e}")

def init_scheduler():
    scheduler.add_job(generate_and_send_daily_reports, CronTrigger(hour=23, minute=0))
    scheduler.add_job(generate_harvest_tasks, CronTrigger(hour=0, minute=1), id='daily_harvest', replace_existing=True)
    scheduler.add_job(schedule_watering_task, CronTrigger(hour=11, minute=0), id='watering', replace_existing=True)
    scheduler.add_job(heartbeat_check, CronTrigger(minute="*"), id='heartbeat_check', replace_existing=True)
    scheduler.add_job(create_weekly_health_check_tasks, CronTrigger(day_of_week='mon', hour=8, minute=0), id='monday_health', replace_existing=True)
    
    scheduler.start()
    
    # Initial trigger for dynamic jobs
    asyncio.get_event_loop().create_task(generate_harvest_tasks())
    print("APScheduler fully initialized with Task Automation!")

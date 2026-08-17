from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from services.scheduler import (
    schedule_watering_task,
    check_missing_work_6pm,
    generate_evening_summary_7pm,
    create_weekly_health_check_tasks
)

router = APIRouter(
    prefix="/api/test/cron",
    tags=["Test Cron Jobs"]
)

@router.post("/watering")
async def test_watering(background_tasks: BackgroundTasks):
    background_tasks.add_task(schedule_watering_task)
    return {"message": "11:00 AM Watering task triggered in background."}

@router.post("/6pm-check")
async def test_6pm_check(background_tasks: BackgroundTasks):
    background_tasks.add_task(check_missing_work_6pm)
    return {"message": "6:00 PM Missing work check triggered in background."}

@router.post("/7pm-summary")
async def test_7pm_summary(background_tasks: BackgroundTasks):
    background_tasks.add_task(generate_evening_summary_7pm)
    return {"message": "7:00 PM Summary and prep triggered in background."}

@router.post("/monday-health")
async def test_monday_health(background_tasks: BackgroundTasks):
    background_tasks.add_task(create_weekly_health_check_tasks)
    return {"message": "Monday 8:00 AM Health Check tasks generation triggered in background."}

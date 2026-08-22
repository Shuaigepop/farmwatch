from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from services.scheduler import (
    schedule_watering_task,
    heartbeat_check,
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

@router.post("/heartbeat")
async def test_heartbeat(background_tasks: BackgroundTasks):
    background_tasks.add_task(heartbeat_check)
    return {"message": "Heartbeat check triggered - will run missing work and summary for matching farms."}

@router.post("/monday-health")
async def test_monday_health(background_tasks: BackgroundTasks):
    background_tasks.add_task(create_weekly_health_check_tasks)
    return {"message": "Monday 8:00 AM Health Check tasks generation triggered in background."}


@router.post("/{farm_id}/revert")
async def revert_schedule(farm_id: int, db: AsyncSession = Depends(get_db)):
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    result = await db.execute(select(models.ProposedSchedule).where(
        models.ProposedSchedule.farm_id == farm_id,
        models.ProposedSchedule.date == today_str
    ))
    schedule = result.scalar_one_or_none()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
        
    schedule.status = "draft"
    await db.commit()
    return {"message": "Schedule reverted to draft"}

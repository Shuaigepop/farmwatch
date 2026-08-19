import asyncio
import sys
sys.path.append('backend')
from database import AsyncSessionLocal
from models.models import LineGroup
from sqlalchemy import select
async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(LineGroup))
        for g in res.scalars().all():
            print(f'GroupID: {g.line_group_id}, FarmID: {g.farm_id}, GroupName: {g.group_name}'.encode('utf-8'))
asyncio.run(main())

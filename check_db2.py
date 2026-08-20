import asyncio
import sys
sys.path.append('backend')
from database import AsyncSessionLocal
from models.models import Farm
from sqlalchemy import select
async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Farm))
        for f in res.scalars().all():
            print(f'FarmID: {f.id}, Name: {f.name}'.encode('utf-8'))
asyncio.run(main())

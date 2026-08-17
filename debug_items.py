import asyncio, sys
sys.path.append('backend')
from database import AsyncSessionLocal
from models.models import InventoryItem
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(InventoryItem))
        items = res.scalars().all()
        for i in items: print(f"Item: {i.name}, FarmID: {i.farm_id}")

asyncio.run(main())

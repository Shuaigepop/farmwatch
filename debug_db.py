import asyncio, pprint, sys
sys.path.append('backend')
from backend.database import AsyncSessionLocal
from backend.models.models import InventoryItem, Farm
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        print("Farms:")
        res = await db.execute(select(Farm))
        farms = res.scalars().all()
        for f in farms: print(f.id, f.name)
        
        print("\nInventoryItems:")
        res = await db.execute(select(InventoryItem))
        items = res.scalars().all()
        for i in items: print(i.id, i.name, i.farm_id)

asyncio.run(main())

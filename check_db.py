import asyncio, pprint
import sys
sys.path.append('backend')
from backend.database import AsyncSessionLocal
from backend.models.models import InventoryItem
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(InventoryItem))
        items = res.scalars().all()
        pprint.pprint([{'id':i.id, 'farm_id':i.farm_id, 'name':i.name} for i in items])

asyncio.run(main())

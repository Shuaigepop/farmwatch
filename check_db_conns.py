import asyncio
import sys
sys.path.append('backend')
from database import AsyncSessionLocal
from sqlalchemy import text
async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(text('SELECT count(*) FROM pg_stat_activity'))
        print('Active connections:', res.scalar())
asyncio.run(main())

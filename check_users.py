import asyncio
import sys
sys.path.append('backend')
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
async def main():
    engine = create_async_engine('postgresql+asyncpg://neondb_owner:n8QjZzRkwD6W@ep-cold-meadow-a1z2h4q5.ap-southeast-1.aws.neon.tech/neondb?ssl=require')
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as db:
        res = await db.execute(text('SELECT id, username, role, display_name FROM users'))
        for r in res.fetchall():
            print(r)
asyncio.run(main())

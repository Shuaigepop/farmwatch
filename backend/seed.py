import asyncio
from passlib.context import CryptContext
from database import init_db, AsyncSessionLocal
from models.models import User, Farm, Task
from datetime import datetime, timedelta

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def seed_data():
    await init_db()
    print("Database initialized.")
    
    async with AsyncSessionLocal() as session:
        # Create Farms
        farm_a = Farm(name="Farm A", location="North", description="Tomato Farm")
        farm_b = Farm(name="Farm B", location="South", description="Corn Farm")
        farm_c = Farm(name="Farm C", location="East", description="Wheat Farm")
        session.add_all([farm_a, farm_b, farm_c])
        await session.commit()
        await session.refresh(farm_a)
        
        # Create Users
        boss = User(
            username="boss",
            password_hash=pwd_context.hash("boss123"),
            role="boss",
            display_name="The Boss"
        )
        supervisor = User(
            username="supervisor",
            password_hash=pwd_context.hash("sup123"),
            role="supervisor",
            display_name="Senior Supervisor"
        )
        leader = User(
            username="leader",
            password_hash=pwd_context.hash("leader123"),
            role="leader",
            display_name="Farm A Leader",
            farm_id=farm_a.id
        )
        session.add_all([boss, supervisor, leader])
        
        # Create Tasks
        task1 = Task(
            farm_id=farm_a.id,
            title="Plant Tomatoes",
            stage="seeding",
            status="in_progress",
            due_date=datetime.utcnow() + timedelta(days=7)
        )
        task2 = Task(
            farm_id=farm_a.id,
            title="Fertilize Soil",
            stage="fertilizing",
            status="pending",
            due_date=datetime.utcnow() + timedelta(days=3)
        )
        session.add_all([task1, task2])
        
        await session.commit()
        print("Seed data created successfully.")

if __name__ == "__main__":
    asyncio.run(seed_data())

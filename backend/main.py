from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from pathlib import Path

from database import init_db, AsyncSessionLocal
from models.models import User, Farm, LineGroup
from routers import auth, webhook, messages, photos, farms, tasks, inventory, reports, deliveries, schedules, liff, test_cron, zone_plans
from services.scheduler import init_scheduler
from passlib.context import CryptContext
from sqlalchemy import select

app = FastAPI(title="FarmWatch API", description="農場管理儀表板 API")

# 前端靜態檔案路徑 (Frontend static files path)
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def force_utf8_charset(request: Request, call_next):
    response = await call_next(request)
    content_type = response.headers.get("Content-Type", "")
    if "javascript" in content_type or "css" in content_type or "html" in content_type:
        if "charset=" not in content_type.lower():
            response.headers["Content-Type"] = f"{content_type}; charset=utf-8"
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@app.on_event("startup")
async def startup_event():
    # Initialize Scheduler
    init_scheduler()
    
    # 初始化資料庫 (Init DB)
    await init_db()
    
    # 建立上傳資料夾 (Create uploads directory)
    os.makedirs("./uploads", exist_ok=True)
    
    # 建立預設資料 (Create default seed data)
    async with AsyncSessionLocal() as session:
        # 针对 PostgreSQL 的线上资料库迁移 (Auto-migration for Render Postgres)
        # Must run BEFORE any queries (like select(Farm)) to avoid UndefinedColumnError
        try:
            from sqlalchemy import text
            await session.execute(text("ALTER TABLE recurring_tasks ADD COLUMN IF NOT EXISTS target_role VARCHAR DEFAULT 'worker';"))
            await session.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS target_role VARCHAR DEFAULT 'worker';"))
            await session.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS verified_by INTEGER;"))
            await session.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS verified_at TIMESTAMP;"))
            
            # New time columns for Farms
            await session.execute(text("ALTER TABLE farms ADD COLUMN IF NOT EXISTS check_time VARCHAR DEFAULT '18:00';"))
            await session.execute(text("ALTER TABLE farms ADD COLUMN IF NOT EXISTS summary_time VARCHAR DEFAULT '19:00';"))
            await session.execute(text("ALTER TABLE farms ADD COLUMN IF NOT EXISTS sop_time VARCHAR DEFAULT '06:00';"))
            
            # New time column for Tasks
            await session.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS notify_time VARCHAR;"))
            
            await session.commit()
            print("Successfully added new columns for Foreman verification and Time Settings.")
        except Exception as e:
            print(f"Migration skipped or failed (safe to ignore if SQLite): {e}")

        # 預設老闆帳號 (Default boss account)
        result = await session.execute(select(User).where(User.username == "admin"))
        if not result.scalar_one_or_none():
            # 建立預設農場 (Create default farms)
            farm_a = Farm(name="北谷農場", location="北區", description="主要種植生菜和番茄")
            farm_b = Farm(name="陽光山農場", location="南區", description="主要種植農田菜")
            farm_c = Farm(name="綠野農場", location="東區", description="混合蔬菜種植")
            session.add_all([farm_a, farm_b, farm_c])
            await session.flush()
            

            # 建立預設使用者 (Create default users)
            admin_user = User(
                username="admin",
                password_hash=pwd_context.hash("admin123"),
                role="boss",
                display_name="老闆",
                language="zh"
            )
            supervisor_user = User(
                username="supervisor",
                password_hash=pwd_context.hash("super123"),
                role="supervisor",
                display_name="王主管",
                language="zh"
            )
            leader_user = User(
                username="leader",
                password_hash=pwd_context.hash("leader123"),
                role="leader",
                display_name="李組長",
                language="zh",
                farm_id=farm_a.id
            )
            session.add_all([admin_user, supervisor_user, leader_user])
            await session.commit()
            print("Default seed data created: 3 farms + 3 users (admin/admin123, supervisor/super123, leader/leader123)")
            
        # Seed NG Limau Kasturi Farm
        try:
            from seed_ipoh_farm import seed_ipoh_farm as do_seed
            await do_seed()
            print("Successfully seeded NG Limau Kasturi Farm")
        except Exception as e:
            print("Failed to seed NG Limau Kasturi Farm:", e)
            


# Include API routers
app.include_router(auth.router)
app.include_router(webhook.router)
app.include_router(messages.router)
app.include_router(photos.router)
app.include_router(farms.router)
app.include_router(tasks.router)
app.include_router(inventory.router)
app.include_router(reports.router)
app.include_router(deliveries.router)
app.include_router(schedules.router)
app.include_router(liff.router)
app.include_router(test_cron.router)
app.include_router(zone_plans.router)

# Serve uploaded files
os.makedirs("./uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Serve frontend static files (CSS, JS)
if FRONTEND_DIR.exists():
    app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
    app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")

    # 前端入口 - 所有非API路徑都返回 index.html (Frontend SPA catch-all)
    @app.get("/")
    async def serve_frontend():
        return FileResponse(
            str(FRONTEND_DIR / "index.html"), 
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
        )

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # 不攔截 API 和上傳路徑 (Don't intercept API and upload paths)
        if full_path.startswith("api/") or full_path.startswith("uploads/"):
            return {"detail": "Not Found"}
        
        # 嘗試直接提供檔案 (Try to serve the file directly)
        file_path = FRONTEND_DIR / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        
        # SPA fallback - 返回 index.html
        return FileResponse(
            str(FRONTEND_DIR / "index.html"),
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
        )
else:
    @app.get("/")
    async def root():
        return {"message": "Welcome to FarmWatch API. Frontend not found at: " + str(FRONTEND_DIR)}

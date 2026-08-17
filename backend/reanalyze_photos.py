"""手动重新分析所有 pending 照片的脚本"""
import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from database import AsyncSessionLocal
from sqlalchemy import select
from models.models import Photo
from services.ai_service import ai_service
from config import settings
import json
from datetime import datetime, timezone

async def reanalyze():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Photo).where(Photo.health_status == "pending")
        )
        photos = result.scalars().all()
        print(f"Found {len(photos)} pending photos to analyze")
        
        for photo in photos:
            full_path = os.path.join(settings.UPLOAD_DIR, photo.file_path)
            print(f"\n--- Analyzing Photo #{photo.id}: {full_path}")
            
            if not os.path.exists(full_path):
                print(f"  [SKIP] File not found: {full_path}")
                continue
            
            try:
                analysis_text = await ai_service.analyze_image(full_path)
                print(f"  [OK] Raw result: {analysis_text[:300]}")
                analysis_data = json.loads(analysis_text)
                
                photo.ai_analysis = analysis_text
                photo.health_status = analysis_data.get("status", "pending")
                photo.analyzed_at = datetime.now(timezone.utc)
                await session.commit()
                print(f"  [SAVED] status={photo.health_status}")
            except Exception as e:
                print(f"  [ERROR] {e}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(reanalyze())

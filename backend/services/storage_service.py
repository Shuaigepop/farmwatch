import os
import uuid
from PIL import Image
from io import BytesIO
from config import settings

class StorageService:
    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        os.makedirs(self.upload_dir, exist_ok=True)
        self.thumbnail_dir = os.path.join(self.upload_dir, "thumbnails")
        os.makedirs(self.thumbnail_dir, exist_ok=True)

    async def save_image(self, content: bytes, original_filename: str) -> str:
        # 儲存圖片 (Save image)
        if settings.CLOUDINARY_URL:
            import cloudinary.uploader
            # cloudinary will handle upload synchronously in a thread or we just block briefly
            # better to run in thread
            import asyncio
            def _upload():
                return cloudinary.uploader.upload(content, folder="farmwatch")
            result = await asyncio.to_thread(_upload)
            return result.get('secure_url')
            
        ext = os.path.splitext(original_filename)[1]
        if not ext:
            ext = ".jpg"
        
        filename = f"{uuid.uuid4().hex}{ext}"
        filepath = os.path.join(self.upload_dir, filename)
        
        with open(filepath, "wb") as f:
            f.write(content)
            
        return filename

    async def create_thumbnail(self, filename: str) -> str:
        if filename.startswith('http'):
            # Cloudinary supports on-the-fly transformations
            # e.g., .../upload/w_300,c_fill/...
            # For simplicity, we just return the original URL, Cloudinary handles thumbnails if we modify the URL,
            # or we can just rely on frontend CSS to scale it. 
            # Or we can insert /upload/w_300/ into the URL.
            if "upload/" in filename:
                return filename.replace("upload/", "upload/w_300,c_limit/")
            return filename
            
        # 建立縮圖 (Create thumbnail)
        filepath = os.path.join(self.upload_dir, filename)
        thumbnail_filename = f"thumb_{filename}"
        thumbnail_path = os.path.join(self.thumbnail_dir, thumbnail_filename)
        
        try:
            with Image.open(filepath) as img:
                img.thumbnail((300, 300))
                img.save(thumbnail_path)
            return thumbnail_filename
        except Exception as e:
            print(f"Error creating thumbnail: {e}")
            return filename # fallback to original

    def get_image_path(self, filename: str, is_thumbnail: bool = False) -> str:
        if is_thumbnail:
            return os.path.join(self.thumbnail_dir, filename)
        return os.path.join(self.upload_dir, filename)

storage_service = StorageService()

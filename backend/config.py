from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    LINE_CHANNEL_SECRET: str = ""
    LINE_CHANNEL_ACCESS_TOKEN: str = ""
    GEMINI_API_KEY: str = ""
    JWT_SECRET_KEY: str = "supersecretkey" # Change in production
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    DATABASE_URL: str = "sqlite+aiosqlite:///./farmwatch.db"
    UPLOAD_DIR: str = "./uploads"
    CLOUDINARY_URL: str = "" # cloudinary://...
    DAILY_REPORT_HOUR: int = 11

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

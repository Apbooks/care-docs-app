from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://careapp:careapp@db:5432/caredb"

    # JWT
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Application
    APP_NAME: str = "Care Documentation App"
    DEBUG: bool = False

    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]

    # File Upload
    MAX_PHOTO_SIZE_MB: int = 10
    PHOTO_UPLOAD_DIR: str = "photos"

    # Push Notifications
    VAPID_PUBLIC_KEY: str = ""
    VAPID_PRIVATE_KEY: str = ""
    VAPID_CLAIM_EMAIL: str = "admin@example.com"

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings():
    return Settings()

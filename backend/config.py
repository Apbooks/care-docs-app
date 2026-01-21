from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache
from typing import Union, List
import sys

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://careapp:careapp@db:5432/caredb"

    # JWT - REQUIRED: Set JWT_SECRET_KEY in environment or .env file
    # Generate with: openssl rand -hex 32
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    REFRESH_TOKEN_EXPIRE_DAYS: int = 3650

    # Application
    APP_NAME: str = "Care Documentation App"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # Options: development, production

    # CORS - Can be a comma-separated string or list
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # File Upload
    MAX_PHOTO_SIZE_MB: int = 10
    PHOTO_UPLOAD_DIR: str = "photos"
    AVATAR_UPLOAD_DIR: str = "avatars"

    # Push Notifications
    VAPID_PUBLIC_KEY: str = ""
    VAPID_PRIVATE_KEY: str = ""
    VAPID_CLAIM_EMAIL: str = "admin@example.com"

    # Reminder Scheduler
    SCHEDULER_ENABLED: bool = True
    REMINDER_SCAN_INTERVAL_SECONDS: int = 60

    # Email (SMTP) for password reset
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""
    SMTP_USE_TLS: bool = True
    SMTP_USE_SSL: bool = False
    FRONTEND_BASE_URL: str = "http://localhost:3000"

    @field_validator('JWT_SECRET_KEY')
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        """Ensure JWT secret is not using insecure defaults"""
        insecure_defaults = [
            "your-secret-key-change-in-production",
            "secret",
            "changeme",
            "default"
        ]
        if v.lower() in insecure_defaults or len(v) < 32:
            print("\n" + "="*70, file=sys.stderr)
            print("SECURITY ERROR: Insecure JWT_SECRET_KEY detected!", file=sys.stderr)
            print("="*70, file=sys.stderr)
            print("The JWT_SECRET_KEY must be at least 32 characters long", file=sys.stderr)
            print("and cannot be a common default value.", file=sys.stderr)
            print("\nGenerate a secure secret with:", file=sys.stderr)
            print("  openssl rand -hex 32", file=sys.stderr)
            print("\nThen set it in your .env file:", file=sys.stderr)
            print("  JWT_SECRET_KEY=<your-generated-secret>", file=sys.stderr)
            print("="*70 + "\n", file=sys.stderr)
            sys.exit(1)
        return v

    def get_cors_origins(self) -> List[str]:
        """Parse CORS_ORIGINS string into a list"""
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
        return self.CORS_ORIGINS

    class Config:
        # Make .env file optional - use environment variables in Docker
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = True
        # Don't fail if .env doesn't exist
        extra = 'ignore'

@lru_cache()
def get_settings():
    return Settings()

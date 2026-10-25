from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    environment: str = "development"
    database_url: str = "sqlite+aiosqlite:///./enterprise.db"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret_key: str = "development-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    webhook_secret: str = "development-webhook-secret"
    gemini_api_key: str | None = None
    outbound_webhook_url: str | None = None
    upload_dir: Path = Path("uploads")
    report_dir: Path = Path("reports")


@lru_cache
def get_settings() -> Settings:
    return Settings()

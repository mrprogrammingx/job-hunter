from pydantic_settings import BaseSettings
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    database_url: str = f"sqlite+aiosqlite:///{PROJECT_ROOT}/data/jobs.db"
    cors_origins: list[str] = ["http://localhost:3000"]
    otel_enabled: bool = False
    otel_endpoint: str = "http://localhost:4317"
    jwt_secret: str = "change-me-before-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days

    model_config = {"env_file": str(PROJECT_ROOT / ".env"), "env_file_encoding": "utf-8"}


settings = Settings()

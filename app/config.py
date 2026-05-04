"""
Configuración central leída desde .env
Usar: from app.config import get_settings; s = get_settings()
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ── MongoDB ──────────────────────────────────────────────────
    MONGO_URI: str
    MONGO_DB_NAME: str = "yoloDB"

    # ── JWT ──────────────────────────────────────────────────────
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── App ──────────────────────────────────────────────────────
    APP_ENV: str = "development"
    DEBUG: bool = True
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # ── Archivos ─────────────────────────────────────────────────
    UPLOAD_FOLDER: str = "uploads"
    MAX_FILE_SIZE_MB: int = 10

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    @property
    def max_file_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()

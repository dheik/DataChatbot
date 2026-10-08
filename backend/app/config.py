"""Configurações da aplicação, lidas do arquivo .env."""
import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _list(value: str) -> list:
    return [v.strip() for v in value.split(",") if v.strip()]


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", ""))
    # Modelo principal + modelos reserva (usados se o principal estiver indisponível)
    gemini_models: list = field(default_factory=lambda: _list(
        os.getenv("GEMINI_MODELS", "gemini-3.8-flash,gemini-2.5-flash")))
    database_path: str = os.getenv("DATABASE_PATH", os.path.join(BASE_DIR, "data", "pokemon.db"))
    max_question_length: int = int(os.getenv("MAX_QUESTION_LENGTH", "300"))
    max_rows: int = int(os.getenv("MAX_ROWS", "50"))
    query_timeout_ms: int = int(os.getenv("QUERY_TIMEOUT_MS", "2000"))
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "20"))
    cors_origins: list = field(default_factory=lambda: _list(os.getenv("CORS_ORIGINS", "*")))


settings = Settings()

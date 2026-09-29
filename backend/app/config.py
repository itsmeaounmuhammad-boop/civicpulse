from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central application configuration, loaded from environment variables
    (or a .env file in local dev). Never read os.environ directly elsewhere
    in the app — always go through this object.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Literal["development", "production", "test"] = "development"

    # --- Database ---
    database_url: str = (
        "postgresql+asyncpg://civicpulse:changeme@localhost:5432/civicpulse"
    )

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"

    # --- Triage provider ---
    triage_provider: Literal["llm", "ollama", "rules", "simulated"] = "simulated"
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.2:1b"

    # --- Rate limiting ---
    rate_limit_per_minute: int = 20

    # --- Misc ---
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings accessor. FastAPI dependency-injects this so tests
    can override it easily without touching real environment variables.
    """
    return Settings()
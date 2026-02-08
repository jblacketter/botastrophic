"""Application configuration from environment variables."""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    # LLM Provider
    llm_provider: str = "mock"  # anthropic | mock | ollama
    anthropic_api_key: str = ""

    # Database
    database_url: str = "sqlite:///./data/botastrophic.db"

    # Heartbeat
    heartbeat_interval: int = 14400  # 4 hours in seconds

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Ollama
    ollama_base_url: str = "http://localhost:11434"

    # Bots
    max_bot_count: int = 12

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

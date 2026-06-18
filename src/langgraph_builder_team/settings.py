from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "LangGraph Builder Team"
    app_env: str = "local"
    quality_threshold: int = 75
    postgres_dsn: str = "postgresql://builder:builder@localhost:5432/builder"
    qdrant_url: str = "http://localhost:6333"
    project_memory_collection: str = "project_memory"
    global_memory_collection: str = "global_meta_knowledge"
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "LangGraph Builder Team"
    app_env: str = "local"
    quality_threshold: int = 75
    postgres_dsn: str = "postgresql://builder:builder@localhost:5432/builder"
    postgres_checkpointer_enabled: bool = True
    qdrant_url: str = "http://localhost:6333"
    project_memory_collection: str = "project_memory"
    global_memory_collection: str = "global_meta_knowledge"
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    llm_provider: str = "openai-compatible"
    llm_base_url: str | None = None
    llm_model: str = "gpt-4o-mini"
    auth_enabled: bool = False
    auth_username: str = "admin"
    auth_password: str | None = None
    auth_session_secret: str = "change-me"
    auth_cookie_name: str = "lgb_session"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()

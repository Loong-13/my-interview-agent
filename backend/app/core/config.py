from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "local"
    app_name: str = "PyOffer Agent API"
    app_secret_key: str = Field(default="change_me", repr=False)
    access_token_expire_minutes: int = 60 * 24 * 7

    database_url: str = "postgresql+psycopg://pyoffer:pyoffer@localhost:5432/pyoffer"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 10

    llm_base_url: str = "https://api.example.com/v1"
    llm_api_key: str = Field(default="replace_me", repr=False)
    llm_model: str = "gpt-4.1-mini"
    embedding_model: str = "text-embedding-3-small"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


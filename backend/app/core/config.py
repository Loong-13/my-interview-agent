"""集中管理从环境变量读取的应用配置。"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 运行环境与应用基本信息。
    app_env: str = "local"
    app_name: str = "PyOffer Agent API"
    app_secret_key: str = Field(default="change_me", repr=False)
    access_token_expire_minutes: int = 60 * 24 * 7

    # 后端依赖的持久化服务配置。
    database_url: str = "postgresql+psycopg://pyoffer:pyoffer@localhost:5432/pyoffer"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # 文件处理与外部 LLM 相关配置。
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 10

    llm_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    llm_api_key: str = Field(default="replace_me", repr=False)
    llm_model: str = "qwen3-max-latest"
    embedding_model: str = "text-embedding-v3"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    # 缓存配置对象，保证各处导入拿到同一份解析结果。
    return Settings()


settings = get_settings()

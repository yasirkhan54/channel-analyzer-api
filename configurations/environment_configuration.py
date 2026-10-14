from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Server settings read from the environment (or a local .env file)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: SecretStr
    youtube_api_key: SecretStr = SecretStr("")
    client_api_key: SecretStr = Field(min_length=1)
    transcript_proxy_url: SecretStr | None = None
    daily_quota_limit: int = 10000
    quota_safety_margin: int = 200
    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60
    shorts_threshold_seconds: int = 180


@lru_cache
def get_settings() -> Settings:
    return Settings()

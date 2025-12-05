"""Application configuration and settings management."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central application settings loaded from environment variables."""

    app_name: str = Field(default="Sales Assistant Platform")
    api_v1_prefix: str = Field(default="/api")

    database_url: str = Field(
        default_factory=lambda: f"sqlite:///{Path.cwd() / 'sales_assistant.db'}"
    )
    database_echo: bool = Field(default=False)

    jwt_secret_key: str = Field(default="change-me", alias="SA_JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expires_minutes: int = Field(default=60 * 12)

    cors_origins: List[str] = Field(default_factory=list)

    allow_open_registration: bool = Field(default=False)
    bidding_async_mode_default: bool = Field(default=False)
    wechat_app_id: Optional[str] = Field(default=None)
    wechat_app_secret: Optional[str] = Field(default=None)

    model_config = {
        "env_file": ".env",
        "env_prefix": "SA_",
        "case_sensitive": False,
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings."""

    return Settings()  # type: ignore[arg-type]


settings = get_settings()
"""Eagerly instantiated settings for modules that prefer direct import."""

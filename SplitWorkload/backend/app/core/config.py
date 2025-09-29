from __future__ import annotations

import functools
import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application runtime configuration loaded from environment variables."""

    def __init__(
        self,
        *,
        model_base_url: Optional[str] = None,
        model_path: Optional[str] = None,
        api_key: Optional[str] = None,
        request_timeout: Optional[float] = None,
        system_prompt: Optional[str] = None,
    ) -> None:
        self.model_base_url = model_base_url or os.getenv("SPLITWORKLOAD_MODEL_BASE_URL")
        self.model_path = model_path or os.getenv("SPLITWORKLOAD_MODEL_PATH")
        self.api_key = api_key or os.getenv("SPLITWORKLOAD_MODEL_API_KEY")
        timeout_env = os.getenv("SPLITWORKLOAD_MODEL_TIMEOUT")
        self.request_timeout = request_timeout or (float(timeout_env) if timeout_env else 45.0)
        self.system_prompt = system_prompt or os.getenv("SPLITWORKLOAD_SYSTEM_PROMPT")

    @property
    def endpoint(self) -> Optional[str]:
        if not self.model_base_url:
            return None
        return self.model_base_url.rstrip("/")


@functools.lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings(
        model_base_url=os.getenv("SPLITWORKLOAD_MODEL_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
        model_path=os.getenv("SPLITWORKLOAD_MODEL_PATH", "qwen3-max"),
    )

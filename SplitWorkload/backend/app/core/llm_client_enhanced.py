"""Enhanced LLM client with retry and logging for SplitWorkload."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx
from cachetools import LRUCache

from backend.app.common.llm_retry import (
    create_llm_retry_decorator,
    log_llm_request,
    log_llm_response,
    safe_timeout,
)

from .config import Settings, get_settings

logger = logging.getLogger(__name__)


class LLMNotConfiguredError(RuntimeError):
    """Raised when the external LLM endpoint has not been configured."""


class LLMResponseFormatError(RuntimeError):
    """Raised when the LLM response cannot be parsed into the expected schema."""


@dataclass
class LLMResult:
    allocations: Dict[str, float]
    analysis: Optional[str]


class EnhancedQwenLLMClient:
    """Enhanced Qwen LLM client with retry logic and structured logging.

    This client wraps the DashScope Qwen API with:
    - Automatic retry with exponential backoff
    - Structured logging of all requests/responses
    - Better timeout handling
    - Request/response caching
    """

    def __init__(
        self,
        settings: Optional[Settings] = None,
        *,
        cache_size: int = 512,
        max_retries: int = 3,
    ) -> None:
        self._settings = settings or get_settings()
        self._cache: LRUCache[str, LLMResult] = LRUCache(maxsize=cache_size)
        self._retry_decorator = create_llm_retry_decorator(
            max_attempts=max_retries,
            min_wait_seconds=2.0,
            max_wait_seconds=30.0,
        )

    def analyze(self, *, prompt: str) -> LLMResult:
        """Analyze requirement with LLM.

        Args:
            prompt: Formatted prompt for role allocation

        Returns:
            LLMResult with role allocations and analysis

        Raises:
            LLMNotConfiguredError: If LLM endpoint not configured
            LLMResponseFormatError: If response format is invalid
        """
        endpoint = self._settings.endpoint
        if not endpoint or not self._settings.model_path:
            raise LLMNotConfiguredError("LLM endpoint 或模型未配置")
        if not self._settings.api_key:
            raise LLMNotConfiguredError("缺少模型 API Key")

        # Check cache first
        if prompt in self._cache:
            logger.debug("LLM cache hit", extra={"prompt_hash": hash(prompt)})
            return self._cache[prompt]

        # Make request with retry
        response = self._post_with_retry(prompt=prompt)
        result = self._parse_response(response)

        # Cache result
        self._cache[prompt] = result
        return result

    def _post_with_retry(self, *, prompt: str) -> Dict[str, Any]:
        """Make HTTP POST request to LLM API with retry logic.

        Args:
            prompt: Formatted prompt

        Returns:
            Raw API response as dict

        Raises:
            LLMNotConfiguredError: If configuration is invalid
            RuntimeError: If request fails after all retries
        """
        url = f"{self._settings.endpoint}/chat/completions"
        model = self._settings.model_path

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._settings.api_key}",
        }

        system_prompt = (
            self._settings.system_prompt
            or "你是一名具备 NESMA 功能点分析和软件造价评估经验的项目规划专家，"
            "需要根据需求说明输出各角色的人月工作量分配，结果必须是 JSON。"
        )

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.15,
            "max_tokens": 1200,
        }

        timeout_value = safe_timeout(self._settings.request_timeout, default=60.0)

        @self._retry_decorator
        def make_request():
            start_time = time.time()

            # Log request
            log_llm_request(
                provider="dashscope",
                model=model,
                metadata={
                    "url": url,
                    "prompt_length": len(prompt),
                },
            )

            try:
                with httpx.Client(timeout=timeout_value) as client:
                    response = client.post(url, json=payload, headers=headers)
                    response.raise_for_status()

                    duration_ms = (time.time() - start_time) * 1000
                    data = response.json()

                    # Log successful response
                    log_llm_response(
                        provider="dashscope",
                        model=model,
                        duration_ms=duration_ms,
                        success=True,
                    )

                    return data

            except httpx.TimeoutException as exc:
                duration_ms = (time.time() - start_time) * 1000
                log_llm_response(
                    provider="dashscope",
                    model=model,
                    duration_ms=duration_ms,
                    success=False,
                    error=f"Timeout after {timeout_value}s",
                )
                raise RuntimeError(f"DashScope 请求超时 ({timeout_value}s)，请稍后再试") from exc

            except httpx.HTTPStatusError as exc:
                duration_ms = (time.time() - start_time) * 1000
                status = exc.response.status_code
                body = exc.response.text[:200]

                log_llm_response(
                    provider="dashscope",
                    model=model,
                    duration_ms=duration_ms,
                    success=False,
                    error=f"HTTP {status}: {body}",
                )
                raise RuntimeError(f"DashScope 请求失败 (HTTP {status}): {body}") from exc

            except httpx.RequestError as exc:
                duration_ms = (time.time() - start_time) * 1000
                log_llm_response(
                    provider="dashscope",
                    model=model,
                    duration_ms=duration_ms,
                    success=False,
                    error=str(exc),
                )
                raise RuntimeError(f"DashScope 请求异常: {exc}") from exc

        return make_request()

    def _parse_response(self, response: Dict[str, Any]) -> LLMResult:
        """Parse LLM API response into LLMResult.

        Args:
            response: Raw API response

        Returns:
            Parsed LLMResult

        Raises:
            LLMResponseFormatError: If response format is invalid
        """
        content: Optional[str] = None

        if "choices" in response:
            first_choice = response["choices"][0]
            if isinstance(first_choice, dict):
                message = first_choice.get("message") or {}
                content = message.get("content")
            else:
                content = str(first_choice)
        elif "output" in response:
            content = response.get("output")
        elif "message" in response:
            content = response.get("message")

        if not content:
            raise LLMResponseFormatError("未能在响应中找到内容字段")

        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            logger.error(
                "LLM response JSON parse error",
                extra={"raw_content": content[:500]},
                exc_info=True,
            )
            raise LLMResponseFormatError("LLM 响应内容不是合法 JSON") from exc

        allocations = {
            role: float(value)
            for role, value in data.items()
            if role in {"product", "frontend", "backend", "test", "ops"}
        }
        if not allocations:
            logger.error(
                "LLM response missing role allocations",
                extra={"parsed_data": data},
            )
            raise LLMResponseFormatError("LLM 响应未包含任何角色工作量")

        analysis = data.get("analysis") or data.get("reason")
        return LLMResult(allocations=allocations, analysis=analysis)

"""Enhanced LLM client with retry and logging for BiddingAssistant."""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, Optional

try:
    import requests  # type: ignore
except Exception:
    requests = None  # type: ignore

from backend.app.common.llm_retry import (
    create_llm_retry_decorator,
    log_llm_request,
    log_llm_response,
    safe_timeout,
)

from .llm import LLMClient as BaseLLMClient

logger = logging.getLogger(__name__)


class EnhancedLLMClient(BaseLLMClient):
    """Enhanced LLM client with retry logic and structured logging.

    This extends the base LLMClient with:
    - Automatic retry with exponential backoff
    - Structured logging of all requests/responses
    - Better timeout handling
    - Request/response tracking
    """

    def __init__(
        self,
        provider: str = "stub",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 90,  # Increased default timeout
        max_retries: int = 3,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            provider=provider,
            model=model,
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            **kwargs,
        )
        self.max_retries = max_retries
        self._retry_decorator = create_llm_retry_decorator(
            max_attempts=max_retries,
            min_wait_seconds=2.0,
            max_wait_seconds=30.0,
        )

    def _request_timeout(self) -> Optional[float]:
        """Return a safe timeout value."""
        return safe_timeout(self.timeout, default=90.0)

    def _call_openai_adaptive(self, prompt_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Call OpenAI with retry and logging."""
        if requests is None:
            raise RuntimeError("requests 库未安装，无法调用 OpenAI 接口")

        api_key = self.api_key or self.options.get("api_key")
        if not api_key:
            raise RuntimeError("缺少 OpenAI API key")

        url = self.base_url or "https://api.openai.com/v1/chat/completions"
        model = self.model or self.options.get("model") or "gpt-4o-mini"

        system_prompt = prompt_payload.get("system")
        messages = prompt_payload.get("messages") or []
        assembled_messages = []
        if system_prompt:
            assembled_messages.append({"role": "system", "content": system_prompt})
        assembled_messages.extend(messages)

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        # Prepare retry with explicit JSON instruction
        base_messages = assembled_messages
        extra_instruction = {
            "role": "system",
            "content": (
                "上一次回答未能生成合法 JSON。请严格按照 JSON 对象输出，"
                "禁止出现代码块、额外说明或未转义的引号，确保能被 json.loads 正常解析。"
            ),
        }

        # Track attempts for logging
        for attempt in range(2):  # Keep original 2-attempt JSON retry logic
            retry_messages = [extra_instruction] + base_messages if attempt > 0 else base_messages

            payload = {
                "model": model,
                "messages": retry_messages,
                "temperature": 0,
                "stream": False,
                "response_format": {"type": "json_object"},
            }

            # Wrap the actual HTTP call with retry decorator
            @self._retry_decorator
            def make_request():
                start_time = time.time()

                # Log request
                log_llm_request(
                    provider=self.provider,
                    model=model,
                    metadata={
                        "url": url,
                        "attempt": attempt + 1,
                        "total_messages": len(retry_messages),
                    },
                )

                try:
                    response = requests.post(
                        url,
                        headers=headers,
                        json=payload,
                        timeout=self._request_timeout(),
                        proxies=self._no_proxy,
                    )
                    response.raise_for_status()

                    duration_ms = (time.time() - start_time) * 1000
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]

                    # Log successful response
                    log_llm_response(
                        provider=self.provider,
                        model=model,
                        duration_ms=duration_ms,
                        success=True,
                        metadata={
                            "attempt": attempt + 1,
                            "response_length": len(content),
                        },
                    )

                    return content

                except requests.Timeout as exc:
                    duration_ms = (time.time() - start_time) * 1000
                    log_llm_response(
                        provider=self.provider,
                        model=model,
                        duration_ms=duration_ms,
                        success=False,
                        error=f"Timeout after {self._request_timeout()}s",
                    )
                    raise RuntimeError("LLM 请求超时，请检查网络或稍后再试") from exc

                except requests.HTTPError as exc:
                    duration_ms = (time.time() - start_time) * 1000
                    status = exc.response.status_code if exc.response is not None else "?"
                    body = exc.response.text if exc.response is not None else ""
                    summary = (body or str(exc)).strip().splitlines()[0][:200]

                    log_llm_response(
                        provider=self.provider,
                        model=model,
                        duration_ms=duration_ms,
                        success=False,
                        error=f"HTTP {status}: {summary}",
                    )
                    raise RuntimeError(f"LLM 请求失败 (HTTP {status}): {summary}") from exc

                except requests.RequestException as exc:
                    duration_ms = (time.time() - start_time) * 1000
                    log_llm_response(
                        provider=self.provider,
                        model=model,
                        duration_ms=duration_ms,
                        success=False,
                        error=str(exc),
                    )
                    raise RuntimeError(f"LLM 请求异常: {exc}") from exc

            try:
                content = make_request()
                parsed = self._parse_adaptive_response(content)
                parsed.setdefault("raw_response", content)
                return parsed

            except RuntimeError as exc:
                message = str(exc)
                # Only retry for JSON parse failures on first attempt
                if "LLM 响应解析失败" in message and attempt == 0:
                    logger.warning(
                        "Adaptive response parse failed on attempt 1, retrying with stricter JSON instructions"
                    )
                    continue
                raise

        # Should never reach here
        raise RuntimeError("LLM adaptive analysis failed after all retry attempts")

    def analyze_adaptive(self, text: str) -> Dict[str, Any]:
        """Analyze with adaptive framework (uses enhanced retry logic)."""
        from .adaptive_prompt import build_adaptive_prompt

        prompt_payload = build_adaptive_prompt(text)
        provider = (self.provider or "stub").lower()

        if provider in {"stub", "mock"}:
            raise RuntimeError("LLM 未配置，无法执行自适应分析")

        if provider in {"openai", "openai_compatible"}:
            return self._call_openai_adaptive(prompt_payload)

        if provider in {"azure_openai", "azure"}:
            # TODO: Implement enhanced Azure version
            return super().analyze_adaptive(text)

        raise NotImplementedError(f"LLM provider '{self.provider}' not implemented")

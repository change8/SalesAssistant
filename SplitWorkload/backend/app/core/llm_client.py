from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx
from cachetools import LRUCache

from SplitWorkload.backend.app.core.config import Settings, get_settings


class LLMNotConfiguredError(RuntimeError):
    """Raised when the external LLM endpoint has not been configured."""


class LLMResponseFormatError(RuntimeError):
    """Raised when the LLM response cannot be parsed into the expected schema."""


@dataclass(slots=True)
class LLMResult:
    allocations: Dict[str, float]
    analysis: Optional[str]


class QwenLLMClient:
    """Client for calling the DashScope compatible completion endpoint."""

    def __init__(
        self,
        settings: Optional[Settings] = None,
        *,
        cache_size: int = 512,
    ) -> None:
        self._settings = settings or get_settings()
        self._cache: LRUCache[str, LLMResult] = LRUCache(maxsize=cache_size)

    def analyze(self, *, prompt: str) -> LLMResult:
        endpoint = self._settings.endpoint
        if not endpoint or not self._settings.model_path:
            raise LLMNotConfiguredError("LLM endpoint 或模型未配置")
        if not self._settings.api_key:
            raise LLMNotConfiguredError("缺少模型 API Key")

        if prompt in self._cache:
            return self._cache[prompt]

        response = self._post(prompt=prompt)
        result = self._parse_response(response)
        self._cache[prompt] = result
        return result

    def _post(self, *, prompt: str) -> Dict[str, Any]:
        url = f"{self._settings.endpoint}/chat/completions"
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
            "model": self._settings.model_path,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.15,
            "max_tokens": 1200,
        }

        with httpx.Client(timeout=self._settings.request_timeout) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()

    def _parse_response(self, response: Dict[str, Any]) -> LLMResult:
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
            raise LLMResponseFormatError("LLM 响应内容不是合法 JSON") from exc

        allocations = {
            role: float(value)
            for role, value in data.items()
            if role in {"product", "frontend", "backend", "test", "ops"}
        }
        if not allocations:
            raise LLMResponseFormatError("LLM 响应未包含任何角色工作量")

        analysis = data.get("analysis") or data.get("reason")
        return LLMResult(allocations=allocations, analysis=analysis)

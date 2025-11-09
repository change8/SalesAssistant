"""Utilities for interacting with the WeChat mini program API."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Any, Dict

import httpx
from Crypto.Cipher import AES  # type: ignore


class WechatAPIError(Exception):
    """Raised when the remote WeChat API returns an error."""


class WechatDecryptError(Exception):
    """Raised when decrypting sensitive data fails."""


@dataclass
class Code2SessionPayload:
    openid: str
    session_key: str
    unionid: str | None = None


class WechatMiniProgramClient:
    """Minimal client for the handful of endpoints we need."""

    def __init__(self, app_id: str, app_secret: str, *, timeout: float = 10.0) -> None:
        self.app_id = app_id
        self.app_secret = app_secret
        self.timeout = timeout

    def code2session(self, code: str) -> Code2SessionPayload:
        """Exchange wx.login code for openid & session_key."""

        params = {
            "appid": self.app_id,
            "secret": self.app_secret,
            "js_code": code,
            "grant_type": "authorization_code",
        }
        try:
            resp = httpx.get(
                "https://api.weixin.qq.com/sns/jscode2session",
                params=params,
                timeout=self.timeout,
            )
        except httpx.HTTPError as exc:  # pragma: no cover - network I/O
            raise WechatAPIError("无法连接微信登录服务") from exc

        data = resp.json()
        errcode = data.get("errcode")
        if errcode not in (None, 0):
            errmsg = data.get("errmsg") or "微信登录失败"
            raise WechatAPIError(f"{errmsg}（{errcode}）")

        try:
            return Code2SessionPayload(
                openid=data["openid"],
                session_key=data["session_key"],
                unionid=data.get("unionid"),
            )
        except KeyError as exc:
            raise WechatAPIError("微信返回数据缺失 openid 或 session_key") from exc

    @staticmethod
    def decrypt_user_data(session_key: str, encrypted_data: str, iv: str) -> Dict[str, Any]:
        """Decrypt encrypted data returned by getPhoneNumber button."""

        try:
            key_bytes = base64.b64decode(session_key)
            iv_bytes = base64.b64decode(iv)
            cipher_text = base64.b64decode(encrypted_data)
            cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
            decrypted = cipher.decrypt(cipher_text)
            # PKCS#7 padding
            pad = decrypted[-1]
            if pad < 1 or pad > 16:
                raise ValueError("非法的填充长度")
            payload = decrypted[:-pad]
            data = json.loads(payload.decode("utf-8"))
        except Exception as exc:  # pragma: no cover - crypto errors hard to simulate
            raise WechatDecryptError("手机号解密失败") from exc
        return data

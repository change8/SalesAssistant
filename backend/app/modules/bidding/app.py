"""Mount the original BiddingAssistant FastAPI app under the unified backend."""

from __future__ import annotations

from typing import Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from BiddingAssistant.backend.app import create_app as create_bidding_app
from backend.app.auth import service as auth_service


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """Ensure requests carry a valid JWT from the unified平台."""

    def __init__(self, app: FastAPI, exempt: Callable[[Request], bool] | None = None) -> None:
        super().__init__(app)
        self._exempt = exempt or (lambda request: False)

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        if request.method == "OPTIONS" or self._exempt(request):
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.lower().startswith("bearer "):
            return JSONResponse({"detail": "未登录或凭证缺失"}, status_code=401)
        token = auth_header[7:].strip()
        try:
            auth_service.verify_token(token)
        except auth_service.AuthenticationError as exc:
            return JSONResponse({"detail": str(exc) or "访问凭证无效"}, status_code=401)
        return await call_next(request)


def get_bidding_subapp() -> FastAPI:
    """Return the original BiddingAssistant FastAPI应用（加入鉴权中间件）。"""

    bidding_app = create_bidding_app()

    def _is_public(request: Request) -> bool:
        path = request.url.path
        # 允许访问内置静态和 web 页面（我们 iframe 内部直接使用本地副本，保留该逻辑以防需要）。
        return path.startswith("/web") or path.startswith("/static") or path in {"/", ""}

    bidding_app.add_middleware(JWTAuthMiddleware, exempt=_is_public)
    return bidding_app

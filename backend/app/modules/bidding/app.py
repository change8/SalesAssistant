"""Mount the original BiddingAssistant FastAPI app under the unified backend."""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# from BiddingAssistant.backend.app import create_app as create_bidding_app
from backend.app.auth import service as auth_service
from backend.app.core.database import SessionLocal
# from backend.app.modules.bidding.task_bridge import build_task_observer
from backend.app.modules.tasks.schemas import TaskType
from backend.app.modules.tasks.service import TaskService

logger = logging.getLogger(__name__)


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
            payload = auth_service.verify_token(token)
        except auth_service.AuthenticationError as exc:
            return JSONResponse({"detail": str(exc) or "访问凭证无效"}, status_code=401)
        request.state.user_id = payload.sub
        return await call_next(request)


def _create_task_metadata(request: Request, context: Dict[str, Any]) -> Dict[str, Any]:
    """Create a unified task entry for bidding analysis requests."""

    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        return {}

    db = SessionLocal()
    service = TaskService(db)
    try:
        filename_raw = context.get("filename") or "标书"
        filename = str(filename_raw)[:80]
        description = f"标书分析 · {filename}"
        task = service.create_task(
            owner_id=user_id,
            task_type=TaskType.BIDDING,
            description=description,
            request_payload=context,
        )
        return {"task_id": task.id, "owner_id": user_id, "filename": filename}
    except Exception as exc:  # pragma: no cover - defensive log
        logger.exception("Failed to create bidding task record: %s", exc)
        return {}
    finally:
        db.close()


def get_bidding_subapp() -> FastAPI:
    """Return the original BiddingAssistant FastAPI应用（加入鉴权中间件）。"""
    
    # Stubbed due to missing BiddingAssistant module
    app = FastAPI()
    @app.get("/")
    def index():
        return {"message": "Bidding Assistant Module Placeholder"}
    return app

    # task_observer = build_task_observer()
    # bidding_app = create_bidding_app(
    #     job_observers=[task_observer],
    #     task_factory=_create_task_metadata,
    # )

    # def _is_public(request: Request) -> bool:
    #     path = request.url.path
    #     # 允许访问内置静态和 web 页面（我们 iframe 内部直接使用本地副本，保留该逻辑以防需要）。
    #     return path.startswith("/web") or path.startswith("/static") or path in {"/", ""}

    # bidding_app.add_middleware(JWTAuthMiddleware, exempt=_is_public)
    # return bidding_app

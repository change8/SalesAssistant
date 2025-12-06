"""Sales Assistant unified FastAPI application."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.auth.router import router as auth_router
from backend.app.core.config import settings
from backend.app.core.database import init_db
from backend.app.modules.bidding.app import get_bidding_subapp
# from backend.app.modules.costing.router import router as costing_router
# from backend.app.modules.workload.router import router as workload_router
from backend.app.tasks.router import router as tasks_router
from backend.app.search.router import router as search_router


def create_app() -> FastAPI:
    init_db()
    app = FastAPI(title=settings.app_name, version="0.1.0")

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    api_prefix = settings.api_v1_prefix.rstrip("/")
    app.include_router(auth_router, prefix=api_prefix)
    app.include_router(tasks_router, prefix=api_prefix)
    app.include_router(search_router, prefix=api_prefix)
    
    # modules with missing dependencies
    # bidding_subapp = get_bidding_subapp()
    # app.mount(f"{api_prefix}/bidding", bidding_subapp)
    # app.include_router(workload_router, prefix=f"{api_prefix}/workload")
    # app.include_router(costing_router, prefix=f"{api_prefix}/costing")
    
    from backend.app.modules.bidding_v2.router import router as bidding_v2_router
    app.include_router(bidding_v2_router, prefix=f"{api_prefix}")

    # Exception Handlers
    from fastapi import Request
    from fastapi.responses import JSONResponse
    from backend.app.auth.service import AuthenticationError, UserAlreadyExistsError, PasswordPolicyError, PasswordResetError

    @app.exception_handler(AuthenticationError)
    async def auth_exception_handler(request: Request, exc: AuthenticationError):
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc)},
        )

    @app.exception_handler(UserAlreadyExistsError)
    async def user_exists_handler(request: Request, exc: UserAlreadyExistsError):
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc)},
        )
    
    @app.exception_handler(PasswordPolicyError)
    async def password_policy_handler(request: Request, exc: PasswordPolicyError):
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc)},
        )

    @app.exception_handler(PasswordResetError)
    async def password_reset_handler(request: Request, exc: PasswordResetError):
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc)},
        )


    frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend" / "web"
    if frontend_dir.exists():
        app.mount("/web", StaticFiles(directory=str(frontend_dir), html=True), name="web")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()

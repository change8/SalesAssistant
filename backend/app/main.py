"""Sales Assistant unified FastAPI application."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.auth.router import router as auth_router
from backend.app.core.config import settings
from backend.app.core.database import init_db
from backend.app.modules.bidding.router import router as bidding_router
from backend.app.modules.costing.router import router as costing_router
from backend.app.modules.workload.router import router as workload_router


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
    app.include_router(bidding_router, prefix=f"{api_prefix}/bidding")
    app.include_router(workload_router, prefix=f"{api_prefix}/workload")
    app.include_router(costing_router, prefix=f"{api_prefix}/costing")

    frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend" / "web"
    if frontend_dir.exists():
        app.mount("/web", StaticFiles(directory=str(frontend_dir), html=True), name="web")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()

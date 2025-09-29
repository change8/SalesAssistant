from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from SplitWorkload.backend.app.api.routes import router as api_router


def create_app() -> FastAPI:
    """Application factory so tests can instantiate the API easily."""
    app = FastAPI(title="SplitWorkload API", version="0.2.0")

    templates = Jinja2Templates(directory="app/templates")
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request) -> HTMLResponse:  # type: ignore[override]
        return templates.TemplateResponse("index.html", {"request": request})

    app.include_router(api_router, prefix="/api")
    return app


app = create_app()

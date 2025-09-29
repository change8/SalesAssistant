"""Top-level package for the unified Sales Assistant backend."""

from backend.app.main import create_app, app  # noqa: F401

__all__ = ["create_app", "app"]

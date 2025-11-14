"""Top-level package for the unified Sales Assistant backend."""

# Note: Avoid importing app here to prevent circular imports during migrations
# Import directly where needed: from backend.app.main import app

__all__ = ["create_app", "app"]


def __getattr__(name):
    """Lazy import to avoid circular dependencies."""
    if name == "app" or name == "create_app":
        from backend.app.main import app as _app, create_app as _create_app
        if name == "app":
            return _app
        return _create_app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

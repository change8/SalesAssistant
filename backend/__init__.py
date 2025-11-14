"""Top-level package for the unified Sales Assistant backend."""

# Use lazy imports to avoid circular dependencies during database migrations
# The app is imported when migrate_db.py imports from backend.app.core.database

__all__ = ["create_app", "app"]


def __getattr__(name):
    """Lazy import to prevent circular dependencies."""
    if name == "app" or name == "create_app":
        from backend.app.main import app as _app, create_app as _create_app
        if name == "app":
            return _app
        return _create_app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

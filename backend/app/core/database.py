"""Database configuration and session management."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from .config import settings


engine = create_engine(settings.database_url, echo=settings.database_echo, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, class_=Session)
Base = declarative_base()


def init_db() -> None:
    """Create database tables."""

    from backend.app.auth import models as auth_models  # noqa: F401  # Ensure models are imported
    from backend.app.modules.tasks import models as task_models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _ensure_user_columns()


def _ensure_user_columns() -> None:
    inspector = sa_inspect(engine)
    if not inspector.has_table("users"):
        return
    existing_columns = {column["name"] for column in inspector.get_columns("users")}
    statements = []
    if "reset_token" not in existing_columns:
        statements.append(text("ALTER TABLE users ADD COLUMN reset_token VARCHAR(128)"))
    if "reset_token_expires_at" not in existing_columns:
        statements.append(text("ALTER TABLE users ADD COLUMN reset_token_expires_at DATETIME"))
    if "wechat_openid" not in existing_columns:
        statements.append(text("ALTER TABLE users ADD COLUMN wechat_openid VARCHAR(64)"))
    if "wechat_unionid" not in existing_columns:
        statements.append(text("ALTER TABLE users ADD COLUMN wechat_unionid VARCHAR(64)"))
    if not statements:
        return
    with engine.begin() as connection:
        for stmt in statements:
            connection.execute(stmt)


@contextmanager
def get_session() -> Iterator[Session]:
    """Context manager yielding a transactional SQLAlchemy session."""

    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

"""Database configuration and session management."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from .config import settings


engine = create_engine(settings.database_url, echo=settings.database_echo, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, class_=Session)
Base = declarative_base()


def init_db() -> None:
    """Create database tables."""

    from backend.app.auth import models as auth_models  # noqa: F401  # Ensure models are imported

    Base.metadata.create_all(bind=engine)


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

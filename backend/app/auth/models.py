"""Authentication models for the unified Sales Assistant backend."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.common.models import TimestampMixin
from backend.app.core.database import Base

if TYPE_CHECKING:
    from backend.app.tasks.models import Task


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    reset_token: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, unique=True, index=True)
    reset_token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    wechat_openid: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, unique=True, index=True)
    wechat_unionid: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, unique=True)
    
    # Optional security fields
    email: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    security_question: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    security_answer: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # New fields for Simple Search pivot
    username: Mapped[Optional[str]] = mapped_column(String(64), unique=True, nullable=True, index=True)
    role: Mapped[str] = mapped_column(String(20), default="user", nullable=False)

    # Relationships
    tasks: Mapped[List["Task"]] = relationship("Task", back_populates="user", lazy="select")

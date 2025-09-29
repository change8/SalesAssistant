"""Pydantic schemas for authentication workflows."""

from __future__ import annotations

from datetime import datetime

from typing import Optional

from pydantic import BaseModel, Field


class UserBase(BaseModel):
    phone: str = Field(..., example="13800000000")
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=128)


class UserRead(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    phone: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    sub: int
    exp: int

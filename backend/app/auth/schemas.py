"""Pydantic schemas for authentication workflows."""

from __future__ import annotations

from datetime import datetime

from typing import Optional

from pydantic import BaseModel, Field, field_validator

import re

PHONE_REGEX = re.compile(r"^1[3-9]\d{9}$")


class UserBase(BaseModel):
    phone: str = Field(..., example="13800000000")
    full_name: Optional[str] = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        phone = value.strip()
        if not phone:
            raise ValueError("手机号不能为空")
        if not PHONE_REGEX.fullmatch(phone):
            raise ValueError("请输入 11 位有效手机号")
        return phone


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        password = value.strip()
        if len(password) < 8:
            raise ValueError("密码至少需要 8 位")
        if len(password) > 64:
            raise ValueError("密码长度不能超过 64 位")
        if not re.search(r"[A-Za-z]", password) or not re.search(r"[0-9]", password):
            raise ValueError("密码需同时包含字母和数字")
        return password


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

    @field_validator("phone")
    @classmethod
    def validate_login_phone(cls, value: str) -> str:
        return UserBase.validate_phone(value)

    @field_validator("password")
    @classmethod
    def validate_login_password(cls, value: str) -> str:
        password = value.strip()
        if not password:
            raise ValueError("密码不能为空")
        return password


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    sub: int
    exp: int

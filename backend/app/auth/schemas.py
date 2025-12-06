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
    password: str = Field(..., min_length=8, max_length=64)
    email: Optional[str] = None
    security_question: Optional[str] = None
    security_answer: Optional[str] = None
    username: Optional[str] = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: Optional[str]) -> Optional[str]:
        if value:
            if len(value) < 3:
                raise ValueError("用户名至少需要 3 个字符")
            if not re.match(r"^[a-zA-Z0-9_]+$", value):
                raise ValueError("用户名只能包含字母、数字和下划线")
        return value

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
    role: str
    username: Optional[str] = None
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
        # Allow both phone and username, so we don't enforce strict phone regex here
        if not value.strip():
            raise ValueError("手机号/用户名不能为空")
        return value

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


class PasswordResetRequest(BaseModel):
    phone: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        return UserBase.validate_phone(value)


class PasswordResetToken(BaseModel):
    reset_token: str
    expires_at: datetime


class PasswordResetConfirm(BaseModel):
    phone: str
    reset_token: str = Field(..., min_length=10, max_length=160)
    new_password: str = Field(..., min_length=8, max_length=64)

    @field_validator("phone")
    @classmethod
    def validate_confirm_phone(cls, value: str) -> str:
        return UserBase.validate_phone(value)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        return UserCreate.validate_password(value)


class PasswordChange(BaseModel):
    current_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=64)

    @field_validator("current_password")
    @classmethod
    def validate_current_password(cls, value: str) -> str:
        password = value.strip()
        if not password:
            raise ValueError("当前密码不能为空")
        return password

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        return UserCreate.validate_password(value)


class WechatLoginRequest(BaseModel):
    login_code: str = Field(..., min_length=1, max_length=128, description="wx.login 返回的 code")
    phone_code: Optional[str] = Field(None, min_length=1, max_length=128, description="getRealtimePhoneNumber 返回的 code (可选，用于静默登录)")

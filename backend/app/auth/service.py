"""Authentication service helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from backend.app.auth import models, schemas
from backend.app.core.config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthenticationError(Exception):
    """Raised when authentication or token verification fails."""


class UserAlreadyExistsError(Exception):
    """Raised when trying to create a user with an existing phone number."""


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_user_by_phone(db: Session, phone: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.phone == phone).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[models.User]:
    return db.get(models.User, user_id)


def create_user(db: Session, user_in: schemas.UserCreate) -> models.User:
    if get_user_by_phone(db, user_in.phone):
        raise UserAlreadyExistsError("手机号已注册")
    user = models.User(
        phone=user_in.phone,
        full_name=user_in.full_name,
        password_hash=hash_password(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, phone: str, password: str) -> models.User:
    user = get_user_by_phone(db, phone)
    if not user or not verify_password(password, user.password_hash):
        raise AuthenticationError("手机号或密码错误")
    if not user.is_active:
        raise AuthenticationError("账号已被禁用")
    return user


def create_access_token(*, subject: int, expires_minutes: Optional[int] = None) -> tuple[str, int]:
    expire_minutes = expires_minutes or settings.jwt_access_token_expires_minutes
    expire_delta = timedelta(minutes=expire_minutes)
    expire_time = datetime.now(tz=timezone.utc) + expire_delta
    payload = {"sub": subject, "exp": expire_time}
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, int(expire_delta.total_seconds())


def verify_token(token: str) -> schemas.TokenPayload:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:  # type: ignore[attr-defined]
        raise AuthenticationError("无效的访问令牌") from exc
    if "sub" not in payload:
        raise AuthenticationError("访问令牌缺少主体信息")
    return schemas.TokenPayload(sub=int(payload["sub"]), exp=int(payload["exp"]))

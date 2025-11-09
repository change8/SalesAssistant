"""Authentication service helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from secrets import compare_digest, token_urlsafe
from typing import Optional, Tuple

import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from backend.app.auth import models, schemas
from backend.app.core.config import settings
from backend.app.utils.wechat import (
    WechatAPIError,
    WechatDecryptError,
    WechatMiniProgramClient,
)


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthenticationError(Exception):
    """Raised when authentication or token verification fails."""


class UserAlreadyExistsError(Exception):
    """Raised when trying to create a user with an existing phone number."""


class PasswordPolicyError(Exception):
    """Raised when a password does not meet backend hashing requirements."""


class PasswordResetError(Exception):
    """Raised when generating or consuming password reset tokens fails."""


def hash_password(password: str) -> str:
    try:
        return pwd_context.hash(password)
    except ValueError as exc:  # passlib raises ValueError for unsupported passwords
        raise PasswordPolicyError("密码不符合安全要求，请检查长度和复杂度") from exc


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_user_by_phone(db: Session, phone: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.phone == phone).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[models.User]:
    return db.get(models.User, user_id)


def get_user_by_wechat_openid(db: Session, openid: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.wechat_openid == openid).first()


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


def issue_password_reset(db: Session, phone: str, *, ttl_minutes: int = 15) -> Tuple[str, datetime]:
    user = get_user_by_phone(db, phone)
    if not user:
        raise PasswordResetError("账号不存在")
    token = token_urlsafe(32)
    expires_at = datetime.now(tz=timezone.utc) + timedelta(minutes=ttl_minutes)
    user.reset_token = token
    user.reset_token_expires_at = expires_at
    db.add(user)
    db.commit()
    db.refresh(user)
    return token, expires_at


def reset_password(db: Session, phone: str, token: str, new_password: str) -> models.User:
    user = get_user_by_phone(db, phone)
    if not user or not user.reset_token:
        raise PasswordResetError("找回密码请求不存在或已失效")
    if not user.reset_token_expires_at or user.reset_token_expires_at < datetime.now(tz=timezone.utc):
        user.reset_token = None
        user.reset_token_expires_at = None
        db.add(user)
        db.commit()
        raise PasswordResetError("重置链接已过期，请重新申请")
    if not compare_digest(user.reset_token, token):
        raise PasswordResetError("重置凭证不正确")

    user.password_hash = hash_password(new_password)
    user.reset_token = None
    user.reset_token_expires_at = None
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def change_password(db: Session, user_id: int, current_password: str, new_password: str) -> models.User:
    user = get_user_by_id(db, user_id)
    if not user:
        raise AuthenticationError("账号不存在")
    if not verify_password(current_password, user.password_hash):
        raise AuthenticationError("当前密码不正确")

    user.password_hash = hash_password(new_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login_with_wechat(
    db: Session,
    *,
    code: str,
    encrypted_data: str,
    iv: str,
) -> models.User:
    """Login or auto-register a user via WeChat mini program authorization."""

    if not settings.wechat_app_id or not settings.wechat_app_secret:
        raise AuthenticationError("后台未配置微信小程序参数，请联系管理员")

    client = WechatMiniProgramClient(settings.wechat_app_id, settings.wechat_app_secret)
    try:
        session_payload = client.code2session(code)
    except WechatAPIError as exc:
        raise AuthenticationError(str(exc)) from exc

    try:
        decrypted = client.decrypt_user_data(
            session_payload.session_key,
            encrypted_data,
            iv,
        )
    except WechatDecryptError as exc:
        raise AuthenticationError(str(exc)) from exc

    phone = decrypted.get("purePhoneNumber") or decrypted.get("phoneNumber")
    if not phone:
        raise AuthenticationError("未能解析手机号，请重新授权")

    user = get_user_by_wechat_openid(db, session_payload.openid)
    if user:
        _update_wechat_metadata(user, session_payload, phone, db)
        return user

    user = get_user_by_phone(db, phone)
    if user:
        # Security: verify this is the same user trying to bind WeChat
        if user.wechat_openid and user.wechat_openid != session_payload.openid:
            raise AuthenticationError(
                "该手机号已绑定其他微信账号。如需更换绑定，请先使用密码登录解绑"
            )
        _bind_wechat_identity(user, session_payload)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    random_password = _generate_random_password()
    new_user = models.User(
        phone=phone,
        full_name=None,
        password_hash=hash_password(random_password),
        wechat_openid=session_payload.openid,
        wechat_unionid=session_payload.unionid,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def _generate_random_password() -> str:
    seed = token_urlsafe(12)
    return f"{seed}A1"


def _bind_wechat_identity(user: models.User, payload) -> None:
    if not user.wechat_openid:
        user.wechat_openid = payload.openid
    if payload.unionid and not user.wechat_unionid:
        user.wechat_unionid = payload.unionid


def _update_wechat_metadata(user: models.User, payload, phone: str, db: Session) -> None:
    changed = False
    if not user.phone:
        user.phone = phone
        changed = True
    if payload.unionid and user.wechat_unionid != payload.unionid:
        user.wechat_unionid = payload.unionid
        changed = True
    if changed:
        db.add(user)
        db.commit()
        db.refresh(user)

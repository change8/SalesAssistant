"""Authentication API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.auth import schemas, service
from backend.app.core import dependencies

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
def register_user(
    payload: schemas.UserCreate,
    db: Session = Depends(dependencies.get_db),
):
    try:
        user = service.create_user(db, payload)
    except service.UserAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except service.PasswordPolicyError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return user


@router.post("/login", response_model=schemas.Token)
def login_user(
    payload: schemas.UserLogin,
    db: Session = Depends(dependencies.get_db),
):
    try:
        user = service.authenticate_user(db, payload.phone, payload.password)
    except service.AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    token, expires_in = service.create_access_token(subject=user.id)
    return schemas.Token(access_token=token, expires_in=expires_in)


@router.post("/wechat-login", response_model=schemas.Token)
def login_wechat_user(
    payload: schemas.WechatLoginRequest,
    db: Session = Depends(dependencies.get_db),
):
    try:
        user = service.login_with_wechat(
            db,
            login_code=payload.login_code,
            phone_code=payload.phone_code,
        )
    except service.AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    token, expires_in = service.create_access_token(subject=user.id)
    return schemas.Token(access_token=token, expires_in=expires_in)


@router.get("/me", response_model=schemas.UserRead)
def get_me(current_user=Depends(dependencies.get_current_user)):
    return current_user


@router.post("/forgot-password", response_model=schemas.PasswordResetToken)
def issue_password_reset(
    payload: schemas.PasswordResetRequest,
    db: Session = Depends(dependencies.get_db),
):
    try:
        token, expires_at = service.issue_password_reset(db, payload.phone)
    except service.PasswordResetError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return schemas.PasswordResetToken(reset_token=token, expires_at=expires_at)


@router.post("/reset-password", response_model=schemas.Token)
def reset_password(
    payload: schemas.PasswordResetConfirm,
    db: Session = Depends(dependencies.get_db),
):
    try:
        user = service.reset_password(db, payload.phone, payload.reset_token, payload.new_password)
    except (service.PasswordResetError, service.PasswordPolicyError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    token, expires_in = service.create_access_token(subject=user.id)
    return schemas.Token(access_token=token, expires_in=expires_in)


@router.post("/change-password", response_model=schemas.Token)
def change_password(
    payload: schemas.PasswordChange,
    current_user=Depends(dependencies.get_current_user),
    db: Session = Depends(dependencies.get_db),
):
    try:
        user = service.change_password(
            db,
            user_id=current_user.id,
            current_password=payload.current_password,
            new_password=payload.new_password,
        )
    except service.AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except service.PasswordPolicyError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    token, expires_in = service.create_access_token(subject=user.id)
    return schemas.Token(access_token=token, expires_in=expires_in)

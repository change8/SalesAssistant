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


@router.get("/me", response_model=schemas.UserRead)
def get_me(current_user=Depends(dependencies.get_current_user)):
    return current_user

"""
routers/users.py — User profile endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse, UserUpdate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать профиль пользователя",
)
def create_user(payload: UserCreate, db: Session = Depends(get_db)) -> UserResponse:
    """Create a new user profile.

    The activity_level field is purely informational — no judgment.
    """
    if db.query(User).filter(User.name == payload.name).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Пользователь с именем '{payload.name}' уже существует.",
        )

    # Hash the password
    user_data = payload.model_dump()
    hashed_password = pwd_context.hash(user_data["password"])
    user_data["password"] = hashed_password

    user = User(**user_data)
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Получить профиль пользователя",
)
def get_user(user_id: int, db: Session = Depends(get_db)) -> UserResponse:
    """Fetch a user profile by ID."""
    user: User | None = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Пользователь #{user_id} не найден.",
        )
    return UserResponse.model_validate(user)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Обновить профиль пользователя",
)
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)) -> UserResponse:
    """Update user attributes."""
    user: User | None = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Пользователь #{user_id} не найден.",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)
        
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить профиль пользователя",
)
def delete_user(user_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a user profile."""
    user: User | None = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Пользователь #{user_id} не найден.",
        )
        
    db.delete(user)
    db.commit()

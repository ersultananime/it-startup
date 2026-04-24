"""
routers/goals.py — Goal creation and retrieval endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Goal, User
from app.schemas import GoalCreate, GoalResponse, GoalUpdate

router = APIRouter(prefix="/goals", tags=["Goals"])


@router.post(
    "/",
    response_model=GoalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать цель",
)
def create_goal(payload: GoalCreate, db: Session = Depends(get_db)) -> GoalResponse:
    """Create an action-based goal for a user.

    Goals are expressed in *actions* (steps, minutes, reps), not in weight
    numbers — keeping things positive and achievable.
    """
    # Ensure the user exists
    user: User | None = db.query(User).filter(User.id == payload.user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Пользователь #{payload.user_id} не найден.",
        )

    goal = Goal(**payload.model_dump())
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return GoalResponse.model_validate(goal)


@router.get(
    "/{goal_id}",
    response_model=GoalResponse,
    summary="Получить цель",
)
def get_goal(goal_id: int, db: Session = Depends(get_db)) -> GoalResponse:
    """Fetch a goal by its ID."""
    goal: Goal | None = db.query(Goal).filter(Goal.id == goal_id).first()
    if goal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Цель #{goal_id} не найдена.",
        )
    return GoalResponse.model_validate(goal)


@router.put(
    "/{goal_id}",
    response_model=GoalResponse,
    summary="Обновить цель",
)
def update_goal(goal_id: int, payload: GoalUpdate, db: Session = Depends(get_db)) -> GoalResponse:
    """Update goal attributes."""
    goal: Goal | None = db.query(Goal).filter(Goal.id == goal_id).first()
    if goal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Цель #{goal_id} не найдена.",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(goal, key, value)
        
    db.commit()
    db.refresh(goal)
    return GoalResponse.model_validate(goal)


@router.delete(
    "/{goal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить цель",
)
def delete_goal(goal_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a goal."""
    goal: Goal | None = db.query(Goal).filter(Goal.id == goal_id).first()
    if goal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Цель #{goal_id} не найдена.",
        )
        
    db.delete(goal)
    db.commit()

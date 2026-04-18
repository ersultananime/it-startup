"""
routers/activity.py — Core activity logging endpoint (POST /log-activity).

Flow:
    1. Validate user and goal exist.
    2. Run Soft Return check (3+ day gap detection).
    3. Sum all previous logs for the goal to compute cumulative progress.
    4. Run Progress Engine → daily_pct, global_pct, ASCII progress bar.
    5. Pick motivational message based on daily_pct.
    6. Persist the new ActivityLog entry.
    7. Return the enriched response.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ActivityLog, Goal, User
from app.motivations import get_motivation
from app.progress import compute_progress
from app.schemas import ActivityLogCreate, ActivityLogResponse
from app.soft_return import check_soft_return

router = APIRouter(tags=["Activity"])


@router.post(
    "/log-activity",
    response_model=ActivityLogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Записать активность",
    description=(
        "Принять данные о тренировке, пересчитать прогресс и вернуть "
        "мотивирующее сообщение. Если пользователь не тренировался 3+ дня — "
        "предложить упрощённую цель без осуждения («Мягкий возврат»)."
    ),
)
def log_activity(
    payload: ActivityLogCreate,
    db: Session = Depends(get_db),
) -> ActivityLogResponse:
    """Record an activity session and compute updated progress.

    Args:
        payload: ``user_id``, ``goal_id``, ``value``, ``unit``.
        db:      Injected database session.

    Returns:
        :class:`ActivityLogResponse` with progress percentages, a visual
        progress bar, a motivational message, and optional Soft Return info.

    Raises:
        HTTPException 404: If the user or goal is not found.
        HTTPException 400: If the goal does not belong to this user.
    """
    # ── 1. Validate entities ────────────────────────────────────────────────
    user: User | None = db.query(User).filter(User.id == payload.user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Пользователь #{payload.user_id} не найден.",
        )

    goal: Goal | None = (
        db.query(Goal)
        .filter(Goal.id == payload.goal_id, Goal.is_active == True)  # noqa: E712
        .first()
    )
    if goal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Активная цель #{payload.goal_id} не найдена.",
        )
    if goal.user_id != payload.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Цель не принадлежит этому пользователю.",
        )

    # ── 2. Soft Return: check for 3+ day gap (BEFORE persisting new log) ───
    soft_return = check_soft_return(payload.user_id, payload.goal_id, db)

    # Use simplified target if Soft Return triggered
    effective_daily_target = (
        soft_return.suggested_daily_target
        if soft_return is not None
        else goal.daily_target
    )

    # ── 3. Compute cumulative value (previous logs + this session) ──────────
    previous_total_row = (
        db.query(func.coalesce(func.sum(ActivityLog.value), 0.0))
        .filter(
            ActivityLog.user_id == payload.user_id,
            ActivityLog.goal_id == payload.goal_id,
        )
        .scalar()
    )
    previous_total: float = float(previous_total_row)
    cumulative_value: float = previous_total + payload.value

    # ── 4. Progress Engine ─────────────────────────────────────────────────
    progress = compute_progress(
        session_value=payload.value,
        daily_target=effective_daily_target,
        cumulative_value=cumulative_value,
        global_target=goal.target_value,
    )

    daily_pct: float = progress["daily_pct"]   # type: ignore[assignment]
    global_pct: float = progress["global_pct"]  # type: ignore[assignment]
    progress_bar: str = progress["progress_bar"]  # type: ignore[assignment]

    # ── 5. Motivational message ────────────────────────────────────────────
    motivation = get_motivation(daily_pct)

    # ── 6. Persist log entry ───────────────────────────────────────────────
    log_entry = ActivityLog(
        user_id=payload.user_id,
        goal_id=payload.goal_id,
        value=payload.value,
        unit=payload.unit,
        daily_pct=daily_pct,
        global_pct=global_pct,
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)

    # ── 7. Return enriched response ────────────────────────────────────────
    return ActivityLogResponse(
        log_id=log_entry.id,
        daily_pct=daily_pct,
        global_pct=global_pct,
        progress_bar=progress_bar,
        motivation=motivation,
        soft_return=soft_return,
    )

"""
soft_return.py — «Мягкий возврат» (Soft Return Algorithm).

If a user has skipped 3 or more consecutive days, the system does NOT scold
them. Instead it detects the gap and proposes a simplified daily target
(50 % of the original) so re-entry feels manageable and stress-free.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models import ActivityLog, Goal
from app.schemas import SoftReturnInfo

# Number of consecutive missed days that triggers Soft Return
SOFT_RETURN_THRESHOLD_DAYS: int = 3

# Multiplier applied to the original daily target to create the simplified goal
SIMPLIFICATION_FACTOR: float = 0.5


def _days_since_last_activity(user_id: int, goal_id: int, db: Session) -> int:
    """Return the number of full days elapsed since the user's last activity log.

    Returns 0 if an activity was logged today, and ``SOFT_RETURN_THRESHOLD_DAYS``
    if no activity has ever been recorded (so first-time users are never flagged).
    """
    last_log: ActivityLog | None = (
        db.query(ActivityLog)
        .filter(
            ActivityLog.user_id == user_id,
            ActivityLog.goal_id == goal_id,
        )
        .order_by(desc(ActivityLog.logged_at))
        .first()
    )

    if last_log is None:
        # First ever activity — nothing to flag
        return 0

    now = datetime.now(timezone.utc)
    last_logged_at = last_log.logged_at

    # Ensure both datetimes are offset-aware before subtracting
    if last_logged_at.tzinfo is None:
        last_logged_at = last_logged_at.replace(tzinfo=timezone.utc)

    delta: timedelta = now - last_logged_at
    return max(0, delta.days)


def check_soft_return(
    user_id: int,
    goal_id: int,
    db: Session,
) -> SoftReturnInfo | None:
    """Analyse the user's recent history and propose a simplified goal if needed.

    Args:
        user_id:  ID of the user logging activity.
        goal_id:  ID of the active goal.
        db:       Active SQLAlchemy session.

    Returns:
        A :class:`SoftReturnInfo` instance when a 3+ day gap is detected,
        or ``None`` if the user is on track.
    """
    days_missed = _days_since_last_activity(user_id, goal_id, db)

    if days_missed < SOFT_RETURN_THRESHOLD_DAYS:
        return None

    goal: Goal | None = db.query(Goal).filter(Goal.id == goal_id).first()
    if goal is None:
        return None

    simplified_target = round(goal.daily_target * SIMPLIFICATION_FACTOR, 1)

    return SoftReturnInfo(
        days_missed=days_missed,
        suggested_daily_target=simplified_target,
        unit=goal.unit,
        message=(
            f"Ты отсутствовал(а) {days_missed} дн. — это нормально, жизнь бывает разная. "
            f"Сегодня попробуй сделать всего {simplified_target} {goal.unit} — "
            "маленький шаг лучше, чем никакого. Ты справишься! 🤗"
        ),
    )

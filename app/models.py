"""
models.py — SQLAlchemy ORM models for the Step by Step platform.

Tables:
    users        — user profile (weight, height, activity level)
    goals        — action-based goals (not weight-loss numbers)
    activity_log — each recorded workout / activity session
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    """Registered user with basic physical profile."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    password: Mapped[str] = mapped_column(String(100), nullable=False)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    height_cm: Mapped[float] = mapped_column(Float, nullable=False)
    # low / medium / high — no judgment, just a calibration point
    activity_level: Mapped[str] = mapped_column(String(20), nullable=False, default="low")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now_utc
    )

    goals: Mapped[list[Goal]] = relationship("Goal", back_populates="user")
    activity_logs: Mapped[list[ActivityLog]] = relationship(
        "ActivityLog", back_populates="user"
    )


class Goal(Base):
    """An action-based goal assigned to a user.

    Examples:
        title="Пройти 3 000 шагов", target_value=3000, unit="steps", daily_target=3000
        title="5 минут зарядки", target_value=150, unit="minutes", daily_target=5
    """

    __tablename__ = "goals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    # Total amount to reach the goal (e.g. 90 000 cumulative steps over a month)
    target_value: Mapped[float] = mapped_column(Float, nullable=False)
    # Amount expected per day
    daily_target: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)  # steps / minutes / reps
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now_utc
    )

    user: Mapped[User] = relationship("User", back_populates="goals")
    activity_logs: Mapped[list[ActivityLog]] = relationship(
        "ActivityLog", back_populates="goal"
    )


class ActivityLog(Base):
    """A single logged activity session for a user / goal pair."""

    __tablename__ = "activity_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    goal_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("goals.id", ondelete="CASCADE"), nullable=False
    )
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    logged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now_utc
    )
    # Calculated and stored at write time for fast reads
    daily_pct: Mapped[float] = mapped_column(Float, default=0.0)
    global_pct: Mapped[float] = mapped_column(Float, default=0.0)

    user: Mapped[User] = relationship("User", back_populates="activity_logs")
    goal: Mapped[Goal] = relationship("Goal", back_populates="activity_logs")

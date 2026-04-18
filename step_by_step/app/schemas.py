"""
schemas.py — Pydantic v2 request/response schemas for the Step by Step API.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ─────────────────────────────────────────────
# User schemas
# ─────────────────────────────────────────────

class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, examples=["Алина"])
    password: str = Field(..., min_length=4, max_length=128, examples=["secret123"])
    weight_kg: float = Field(..., gt=0, le=500, examples=[95.0])
    height_cm: float = Field(..., gt=0, le=300, examples=[168.0])
    activity_level: str = Field(
        default="low",
        pattern="^(low|medium|high)$",
        examples=["low"],
    )


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100, examples=["Алина"])
    weight_kg: Optional[float] = Field(None, gt=0, le=500, examples=[95.0])
    height_cm: Optional[float] = Field(None, gt=0, le=300, examples=[168.0])
    activity_level: Optional[str] = Field(
        None,
        pattern="^(low|medium|high)$",
        examples=["low"],
    )


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    weight_kg: float
    height_cm: float
    activity_level: str
    created_at: datetime


# ─────────────────────────────────────────────
# Goal schemas
# ─────────────────────────────────────────────

class GoalCreate(BaseModel):
    user_id: int = Field(..., gt=0)
    title: str = Field(..., min_length=3, max_length=200, examples=["Пройти 3 000 шагов"])
    target_value: float = Field(..., gt=0, examples=[90_000.0])
    daily_target: float = Field(..., gt=0, examples=[3_000.0])
    unit: str = Field(..., min_length=1, max_length=50, examples=["steps"])


class GoalUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200, examples=["Пройти 3 000 шагов"])
    target_value: Optional[float] = Field(None, gt=0, examples=[90_000.0])
    daily_target: Optional[float] = Field(None, gt=0, examples=[3_000.0])
    unit: Optional[str] = Field(None, min_length=1, max_length=50, examples=["steps"])
    is_active: Optional[bool] = None



class GoalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    target_value: float
    daily_target: float
    unit: str
    is_active: bool
    created_at: datetime


# ─────────────────────────────────────────────
# Activity schemas
# ─────────────────────────────────────────────

class ActivityLogCreate(BaseModel):
    user_id: int = Field(..., gt=0)
    goal_id: int = Field(..., gt=0)
    value: float = Field(..., gt=0, examples=[1500.0])
    unit: str = Field(..., min_length=1, max_length=50, examples=["steps"])


class SoftReturnInfo(BaseModel):
    """Returned when the user had a 3+ day gap — suggests a simplified goal."""

    days_missed: int
    suggested_daily_target: float
    unit: str
    message: str


class ActivityLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    log_id: int
    daily_pct: float
    global_pct: float
    progress_bar: str
    motivation: str
    soft_return: Optional[SoftReturnInfo] = None

"""
main.py — FastAPI application entry point for the Step by Step platform.

Run with:
    uvicorn app.main:app --reload
"""

from __future__ import annotations

from fastapi import FastAPI

from app.database import Base, engine
from app.routers import activity, goals, users

# Create all database tables on startup (idempotent)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Step by Step",
    description=(
        "🏃 Платформа мягкого фитнеса: цели в действиях, прогресс-бары "
        "и алгоритм «Мягкого возврата» — без осуждения, без стресса."
    ),
    version="1.0.0",
    contact={"name": "Step by Step Team"},
)

# Register routers
app.include_router(users.router)
app.include_router(goals.router)
app.include_router(activity.router)


@app.get("/", tags=["Root"], summary="Статус сервиса")
def root() -> dict[str, str]:
    """Health-check endpoint."""
    return {
        "service": "Step by Step",
        "status": "running",
        "docs": "/docs",
    }

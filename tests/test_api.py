"""
tests/test_api.py — Integration tests for all three API endpoints.

Uses FastAPI's TestClient with SQLAlchemy StaticPool so that create_all() and
all test sessions share the exact same in-memory SQLite connection.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

# StaticPool reuses a single underlying connection → all sessions see same DB
_test_engine = create_engine(
    "sqlite://",  # bare sqlite:// == in-memory, no file
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSession = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=_test_engine,
)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    """Create tables on the shared in-memory DB before each test."""
    Base.metadata.create_all(bind=_test_engine)
    yield
    Base.metadata.drop_all(bind=_test_engine)




# ── Helper factories ───────────────────────────────────────────────────────

def _create_user(name: str = "Алина") -> dict:
    resp = client.post(
        "/users/",
        json={
            "name": name,
            "password": "strongpassword123",
            "weight_kg": 95.0,
            "height_cm": 168.0,
            "activity_level": "low",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _create_goal(user_id: int) -> dict:
    resp = client.post(
        "/goals/",
        json={
            "user_id": user_id,
            "title": "Пройти 3 000 шагов",
            "target_value": 90_000.0,
            "daily_target": 3_000.0,
            "unit": "steps",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# ── Users ──────────────────────────────────────────────────────────────────

class TestUsers:
    def test_create_user_success(self) -> None:
        data = _create_user()
        assert data["name"] == "Алина"
        assert data["activity_level"] == "low"
        assert "id" in data

    def test_create_duplicate_user_returns_409(self) -> None:
        _create_user("Дубль")
        resp = client.post(
            "/users/",
            json={"name": "Дубль", "password": "strongpassword123", "weight_kg": 70.0, "height_cm": 170.0},
        )
        assert resp.status_code == 409

    def test_get_user_not_found(self) -> None:
        resp = client.get("/users/9999")
        assert resp.status_code == 404


# ── Goals ──────────────────────────────────────────────────────────────────

class TestGoals:
    def test_create_goal_success(self) -> None:
        user = _create_user()
        goal = _create_goal(user["id"])
        assert goal["title"] == "Пройти 3 000 шагов"
        assert goal["unit"] == "steps"

    def test_create_goal_for_missing_user(self) -> None:
        resp = client.post(
            "/goals/",
            json={
                "user_id": 9999,
                "title": "Test",
                "target_value": 1000,
                "daily_target": 100,
                "unit": "steps",
            },
        )
        assert resp.status_code == 404


# ── Activity ───────────────────────────────────────────────────────────────

class TestLogActivity:
    def _log(self, user_id: int, goal_id: int, value: float = 1_500) -> dict:
        resp = client.post(
            "/log-activity",
            json={
                "user_id": user_id,
                "goal_id": goal_id,
                "value": value,
                "unit": "steps",
            },
        )
        assert resp.status_code == 201, resp.text
        return resp.json()

    def test_log_activity_returns_correct_fields(self) -> None:
        user = _create_user()
        goal = _create_goal(user["id"])
        data = self._log(user["id"], goal["id"])
        assert "daily_pct" in data
        assert "global_pct" in data
        assert "progress_bar" in data
        assert "motivation" in data

    def test_half_daily_goal(self) -> None:
        user = _create_user()
        goal = _create_goal(user["id"])
        data = self._log(user["id"], goal["id"], value=1_500)
        assert data["daily_pct"] == 50.0

    def test_full_daily_goal(self) -> None:
        user = _create_user()
        goal = _create_goal(user["id"])
        data = self._log(user["id"], goal["id"], value=3_000)
        assert data["daily_pct"] == 100.0

    def test_progress_bar_contains_blocks(self) -> None:
        user = _create_user()
        goal = _create_goal(user["id"])
        data = self._log(user["id"], goal["id"], value=1_500)
        assert "[" in data["progress_bar"] and "%" in data["progress_bar"]

    def test_invalid_user_returns_404(self) -> None:
        user = _create_user()
        goal = _create_goal(user["id"])
        resp = client.post(
            "/log-activity",
            json={"user_id": 9999, "goal_id": goal["id"], "value": 100, "unit": "steps"},
        )
        assert resp.status_code == 404

    def test_soft_return_none_on_first_log(self) -> None:
        """First-ever log should never trigger Soft Return."""
        user = _create_user()
        goal = _create_goal(user["id"])
        data = self._log(user["id"], goal["id"])
        assert data["soft_return"] is None

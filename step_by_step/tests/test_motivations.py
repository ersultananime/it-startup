"""
tests/test_motivations.py — Unit tests for motivational message bands.
"""

from app.motivations import get_motivation


def test_low_band() -> None:
    msg = get_motivation(0)
    assert "🌱" in msg


def test_low_band_boundary() -> None:
    msg = get_motivation(20)
    assert "🌱" in msg


def test_medium_band() -> None:
    msg = get_motivation(21)
    assert "💪" in msg


def test_medium_band_boundary() -> None:
    msg = get_motivation(50)
    assert "💪" in msg


def test_high_band() -> None:
    msg = get_motivation(51)
    assert "🔥" in msg


def test_near_complete() -> None:
    msg = get_motivation(99)
    assert "🔥" in msg


def test_complete() -> None:
    msg = get_motivation(100)
    assert "🏆" in msg


def test_over_complete() -> None:
    msg = get_motivation(120)
    assert "🏆" in msg

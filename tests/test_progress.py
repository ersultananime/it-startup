"""
tests/test_progress.py — Unit tests for the Progress Engine.
"""

import pytest

from app.progress import compute_progress, render_progress_bar


class TestRenderProgressBar:
    def test_empty_bar(self) -> None:
        assert render_progress_bar(0) == "[░░░░░░░░░░] 0%"

    def test_half_bar(self) -> None:
        assert render_progress_bar(50) == "[█████░░░░░] 50%"

    def test_full_bar(self) -> None:
        assert render_progress_bar(100) == "[██████████] 100%"

    def test_over_100_capped(self) -> None:
        # Bar should not exceed 100 % visually
        result = render_progress_bar(150)
        assert result == "[██████████] 100%"

    def test_small_progress_still_shows_block(self) -> None:
        # 15 % → 2 filled blocks (round(0.15 * 10) = 2 — better than 1)
        result = render_progress_bar(15)
        # At least one filled block must be visible
        assert "█" in result


class TestComputeProgress:
    def test_50_percent_daily(self) -> None:
        result = compute_progress(
            session_value=1_500,
            daily_target=3_000,
            cumulative_value=1_500,
            global_target=90_000,
        )
        assert result["daily_pct"] == 50.0
        assert "50%" in result["progress_bar"]

    def test_global_pct_accumulates(self) -> None:
        result = compute_progress(
            session_value=3_000,
            daily_target=3_000,
            cumulative_value=9_000,
            global_target=90_000,
        )
        assert result["global_pct"] == 10.0

    def test_over_daily_target_capped_at_100(self) -> None:
        result = compute_progress(
            session_value=5_000,
            daily_target=3_000,
            cumulative_value=5_000,
            global_target=90_000,
        )
        assert result["daily_pct"] == 100.0

    def test_progress_bar_included(self) -> None:
        result = compute_progress(
            session_value=300,
            daily_target=3_000,
            cumulative_value=300,
            global_target=90_000,
        )
        assert "progress_bar" in result
        assert "[" in result["progress_bar"]

"""
progress.py — Progress Engine for the Step by Step platform.

Responsibilities:
    - Calculate daily_pct and global_pct from raw activity values.
    - Render a visual ASCII progress bar that fills even from minimal input.
"""

from __future__ import annotations

BAR_LENGTH = 10  # total number of block characters in the bar


def render_progress_bar(pct: float, length: int = BAR_LENGTH) -> str:
    """Render an ASCII progress bar capped at 100 %.

    Args:
        pct:    Percentage to represent (0–100+).
        length: Total bar width in characters.

    Returns:
        A string like ``[████░░░░░░] 42%``

    Example::

        >>> render_progress_bar(0)
        '[░░░░░░░░░░]  0%'
        >>> render_progress_bar(50)
        '[█████░░░░░] 50%'
        >>> render_progress_bar(100)
        '[██████████] 100%'
    """
    filled = min(int(round(pct / 100 * length)), length)
    empty = length - filled
    bar = "█" * filled + "░" * empty
    return f"[{bar}] {min(round(pct), 100)}%"


def compute_progress(
    session_value: float,
    daily_target: float,
    cumulative_value: float,
    global_target: float,
) -> dict[str, float | str]:
    """Calculate progress percentages and return a rendered progress bar.

    The bar is guaranteed to visually advance by at least 1 block for any
    positive ``session_value``, so even tiny efforts feel rewarding.

    Args:
        session_value:    Value logged in **this** session.
        daily_target:     Amount expected today (may be reduced by Soft Return).
        cumulative_value: Sum of all values logged for this goal so far
                          (including the current session).
        global_target:    Total goal target (e.g. 90 000 steps over a month).

    Returns:
        dict with keys:
            ``daily_pct``     – percentage of today's target reached
            ``global_pct``    – percentage of the overall goal reached
            ``progress_bar``  – ASCII bar representing daily_pct
    """
    daily_pct: float = min(round((session_value / daily_target) * 100, 1), 100.0)
    global_pct: float = min(round((cumulative_value / global_target) * 100, 1), 100.0)

    return {
        "daily_pct": daily_pct,
        "global_pct": global_pct,
        "progress_bar": render_progress_bar(daily_pct),
    }

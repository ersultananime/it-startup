"""
motivations.py — Motivational messages keyed by daily progress percentage.

Rules:
    0  –  20 % → gentle encouragement (any step counts)
    21 –  50 % → positive momentum
    51 –  99 % → near completion
    100 %+     → celebration
"""

from __future__ import annotations


def get_motivation(daily_pct: float) -> str:
    """Return a motivational message based on the percentage of the daily goal reached.

    Args:
        daily_pct: Percentage of today's goal completed (0–100+).

    Returns:
        A supportive, non-judgmental motivational string.
    """
    if daily_pct >= 100:
        return (
            "🏆 Цель дня выполнена! Ты доказал(а) себе, что можешь. "
            "Это уже победа — гордись собой!"
        )
    if daily_pct >= 51:
        return (
            "🔥 Ты почти у цели! Больше половины уже позади — "
            "ещё совсем чуть-чуть, и ты там."
        )
    if daily_pct >= 21:
        return (
            "💪 Отличный старт! Ты уже набираешь ритм — "
            "продолжай в том же духе, и результат придёт."
        )
    # 0–20 %
    return (
        "🌱 Любой шаг — уже победа. "
        "Ты начал(а), и это самое важное. Идём дальше!"
    )

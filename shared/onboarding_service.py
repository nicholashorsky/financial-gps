"""Onboarding state helpers."""

from __future__ import annotations

import sqlite3


def get_onboarding_status(conn: sqlite3.Connection, user_id: int) -> dict[str, object]:
    transaction_count = int(
        conn.execute("SELECT COUNT(*) FROM transactions WHERE user_id = ?", (user_id,)).fetchone()[0]
    )
    goal_count = int(conn.execute("SELECT COUNT(*) FROM goals WHERE user_id = ?", (user_id,)).fetchone()[0])
    profile = conn.execute("SELECT province, date_of_birth FROM fire_profiles WHERE user_id = ?", (user_id,)).fetchone()
    has_fire_profile = bool(profile and profile["province"] and profile["date_of_birth"])
    has_income_defaults = int(
        conn.execute("SELECT COUNT(*) FROM fire_income_sources WHERE user_id = ?", (user_id,)).fetchone()[0]
    ) > 0
    steps = [
        {"label": "Import transactions", "done": transaction_count > 0},
        {"label": "Create a goal", "done": goal_count > 0},
        {"label": "Set FIRE profile basics", "done": has_fire_profile},
        {"label": "Review FIRE income defaults", "done": has_income_defaults},
    ]
    complete_count = sum(1 for step in steps if step["done"])
    return {
        "transaction_count": transaction_count,
        "goal_count": goal_count,
        "has_fire_profile": has_fire_profile,
        "has_income_defaults": has_income_defaults,
        "steps": steps,
        "complete_count": complete_count,
        "is_complete": complete_count == len(steps),
        "should_prompt_fire": transaction_count > 0 and not has_fire_profile,
    }


def should_force_onboarding(conn: sqlite3.Connection, user_id: int) -> bool:
    status = get_onboarding_status(conn, user_id)
    return status["transaction_count"] == 0

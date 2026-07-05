"""Bridge status helpers."""

from __future__ import annotations

import sqlite3


def get_bridge_status(conn: sqlite3.Connection, user_id: int) -> dict[str, object]:
    """Return a compact snapshot of FIRE defaults derived from CSVs."""

    last_income_sync = conn.execute(
        """
        SELECT MAX(csv_derived_at) AS last_sync
        FROM fire_income_sources
        WHERE user_id = ?
        """,
        (user_id,),
    ).fetchone()["last_sync"]
    last_spending_sync = conn.execute(
        """
        SELECT MAX(csv_derived_at) AS last_sync
        FROM fire_spending_baseline
        WHERE user_id = ?
        """,
        (user_id,),
    ).fetchone()["last_sync"]
    return {
        "last_sync": max(filter(None, [last_income_sync, last_spending_sync]), default=None),
        "income_rows": conn.execute(
            "SELECT COUNT(*) FROM fire_income_sources WHERE user_id = ?",
            (user_id,),
        ).fetchone()[0],
        "spending_rows": conn.execute(
            "SELECT COUNT(*) FROM fire_spending_baseline WHERE user_id = ?",
            (user_id,),
        ).fetchone()[0],
    }

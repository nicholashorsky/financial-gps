"""Hybrid bridge from budget transactions into FIRE defaults."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
import sqlite3
from uuid import uuid4

from shared.models import BridgeResult
from shared.utils import utc_now_iso


def _days_ago(days: int) -> str:
    return (date.today() - timedelta(days=days)).isoformat()


def _income_defaults(conn: sqlite3.Connection, user_id: int) -> tuple[float, int]:
    rows = conn.execute(
        """
        SELECT amount
        FROM transactions
        WHERE user_id = ?
          AND is_excluded = 0
          AND amount > 0
          AND date >= ?
        ORDER BY date DESC
        """,
        (user_id, _days_ago(90)),
    ).fetchall()
    monthly = round(sum(float(row["amount"] or 0) for row in rows) / 3, 2) if rows else 0.0
    return monthly, len(rows)


def _spending_defaults(conn: sqlite3.Connection, user_id: int) -> dict[str, float]:
    rows = conn.execute(
        """
        SELECT category, ABS(amount) AS amount
        FROM transactions
        WHERE user_id = ?
          AND is_excluded = 0
          AND amount < 0
          AND COALESCE(transaction_type, 'expense') = 'expense'
          AND COALESCE(category, 'Uncategorized') NOT IN ('Transfer', 'Income')
          AND date >= ?
        """,
        (user_id, _days_ago(90)),
    ).fetchall()
    by_category: dict[str, float] = defaultdict(float)
    for row in rows:
        by_category[(row["category"] or "Other")] += float(row["amount"] or 0)
    return {category: round(total / 3, 2) for category, total in by_category.items()}


def _upsert_income_default(conn: sqlite3.Connection, user_id: int, annual_amount: float) -> None:
    row = conn.execute(
        """
        SELECT id, annual_amount, is_override
        FROM fire_income_sources
        WHERE user_id = ? AND source_type = 'employment'
        """,
        (user_id,),
    ).fetchone()
    if row and int(row["is_override"] or 0) == 1:
        return
    if row:
        conn.execute(
            """
            UPDATE fire_income_sources
            SET annual_amount = ?, income_character = 'employment', start_year = COALESCE(start_year, ?),
                is_pensionable = 1, is_override = 0, csv_derived_at = ?
            WHERE id = ?
            """,
            (annual_amount, date.today().year, utc_now_iso(), row["id"]),
        )
    else:
        conn.execute(
            """
            INSERT INTO fire_income_sources (
                id, user_id, source_type, annual_amount, income_character,
                start_year, is_pensionable, is_override, csv_derived_at
            )
            VALUES (?, ?, 'employment', ?, 'employment', ?, 1, 0, ?)
            """,
            (str(uuid4()), user_id, annual_amount, date.today().year, utc_now_iso()),
        )


def _upsert_spending_defaults(conn: sqlite3.Connection, user_id: int, monthly_by_category: dict[str, float]) -> int:
    updated = 0
    categories = list(monthly_by_category)
    if categories:
        placeholders = ", ".join("?" for _ in categories)
        cursor = conn.execute(
            f"""
            DELETE FROM fire_spending_baseline
            WHERE user_id = ?
              AND is_override = 0
              AND category NOT IN ({placeholders})
            """,
            (user_id, *categories),
        )
    else:
        cursor = conn.execute(
            """
            DELETE FROM fire_spending_baseline
            WHERE user_id = ? AND is_override = 0
            """,
            (user_id,),
        )
    updated += max(cursor.rowcount, 0)
    for category, monthly_amount in monthly_by_category.items():
        row = conn.execute(
            """
            SELECT id, is_override
            FROM fire_spending_baseline
            WHERE user_id = ? AND category = ?
            """,
            (user_id, category),
        ).fetchone()
        if row and int(row["is_override"] or 0) == 1:
            continue
        if row:
            conn.execute(
                """
                UPDATE fire_spending_baseline
                SET monthly_amount = ?, is_essential = CASE WHEN ? >= 1000 THEN 1 ELSE 0 END,
                    is_override = 0, csv_derived_at = ?
                WHERE id = ?
                """,
                (monthly_amount, monthly_amount, utc_now_iso(), row["id"]),
            )
        else:
            conn.execute(
                """
                INSERT INTO fire_spending_baseline (
                    id, user_id, category, monthly_amount, is_essential, is_override, csv_derived_at
                )
                VALUES (?, ?, ?, ?, ?, 0, ?)
                """,
                (str(uuid4()), user_id, category, monthly_amount, 1 if monthly_amount >= 1000 else 0, utc_now_iso()),
            )
        updated += 1
    return updated


def sync_fire_defaults(conn: sqlite3.Connection, user_id: int) -> BridgeResult:
    """
    Sync CSV-derived spending and income into FIRE default tables.

    User overrides are preserved.
    """

    monthly_income, income_rows = _income_defaults(conn, user_id)
    monthly_spending = _spending_defaults(conn, user_id)

    fields_updated = 0
    fields_preserved = 0
    warnings: list[str] = []

    if income_rows:
        _upsert_income_default(conn, user_id, monthly_income * 12)
        fields_updated += 1
    else:
        warnings.append("No income transactions found in the last 90 days.")

    if monthly_spending:
        fields_updated += _upsert_spending_defaults(conn, user_id, monthly_spending)
    else:
        warnings.append("No spending transactions found in the last 90 days.")

    preserved_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM fire_income_sources
        WHERE user_id = ? AND is_override = 1
        """,
        (user_id,),
    ).fetchone()[0]
    preserved_count += conn.execute(
        """
        SELECT COUNT(*)
        FROM fire_spending_baseline
        WHERE user_id = ? AND is_override = 1
        """,
        (user_id,),
    ).fetchone()[0]
    fields_preserved += int(preserved_count or 0)

    conn.commit()
    return BridgeResult(
        income_synced=bool(income_rows),
        categories_synced=len(monthly_spending),
        fields_updated=fields_updated,
        fields_preserved=fields_preserved,
        warnings=warnings,
    )

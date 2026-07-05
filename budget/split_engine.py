"""Split transaction helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
from uuid import uuid4
import sqlite3


@dataclass(frozen=True)
class SplitLine:
    amount: float
    category: str
    description: str | None = None


def _transaction_row(conn: sqlite3.Connection, transaction_id: int) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM transactions WHERE id = ?",
        (transaction_id,),
    ).fetchone()


def split_transaction(
    conn: sqlite3.Connection,
    user_id: int,
    transaction_id: int,
    split_lines: Iterable[SplitLine],
) -> int:
    """
    Create a split group and materialize split child transactions.

    The parent transaction is marked excluded so the children drive totals instead.
    """

    parent = _transaction_row(conn, transaction_id)
    if parent is None:
        raise ValueError(f"Transaction {transaction_id} not found.")
    if int(parent["user_id"]) != int(user_id):
        raise ValueError("Transaction does not belong to the current user.")

    lines = list(split_lines)
    if len(lines) < 2:
        raise ValueError("A split needs at least two lines.")

    total = round(sum(line.amount for line in lines), 2)
    parent_amount = round(float(parent["amount"] or 0), 2)
    if abs(total - parent_amount) > 0.01:
        raise ValueError(f"Split total {total:.2f} must equal parent amount {parent_amount:.2f}.")

    cursor = conn.execute(
        "INSERT INTO split_groups (user_id, parent_txn_id) VALUES (?, ?)",
        (user_id, transaction_id),
    )
    split_group_id = int(cursor.lastrowid)

    conn.execute(
        "UPDATE transactions SET is_excluded = 1, split_group_id = ? WHERE id = ?",
        (split_group_id, transaction_id),
    )

    for line in lines:
        conn.execute(
            """
            INSERT INTO transactions (
                user_id, account_id, date, description, amount, category,
                transaction_type, is_recurring, is_excluded, split_group_id,
                source, raw_description
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, ?, 'manual_split', ?)
            """,
            (
                user_id,
                parent["account_id"],
                parent["date"],
                line.description or parent["description"],
                line.amount,
                line.category,
                "expense" if line.amount < 0 else "income",
                split_group_id,
                parent["raw_description"] or parent["description"] or "",
            ),
        )

    conn.commit()
    return split_group_id


def remove_split_group(conn: sqlite3.Connection, split_group_id: int) -> None:
    """Restore the parent transaction and delete generated split rows."""

    parent = conn.execute(
        "SELECT parent_txn_id FROM split_groups WHERE id = ?",
        (split_group_id,),
    ).fetchone()
    if parent is None:
        return

    conn.execute("DELETE FROM transactions WHERE split_group_id = ?", (split_group_id,))
    conn.execute(
        "UPDATE transactions SET is_excluded = 0, split_group_id = NULL WHERE id = ?",
        (parent["parent_txn_id"],),
    )
    conn.execute("DELETE FROM split_groups WHERE id = ?", (split_group_id,))
    conn.commit()

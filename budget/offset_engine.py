"""Generic offset helpers for reimbursements and manual corrections."""

from __future__ import annotations

import sqlite3


def create_offset_pair(
    conn: sqlite3.Connection,
    user_id: int,
    primary_txn_id: int,
    offset_txn_id: int,
) -> int:
    """Link two transactions as an offset pair using the cash_offsets table."""

    primary_row = conn.execute(
        "SELECT id, user_id FROM transactions WHERE id = ?",
        (primary_txn_id,),
    ).fetchone()
    offset_row = conn.execute(
        "SELECT id, user_id FROM transactions WHERE id = ?",
        (offset_txn_id,),
    ).fetchone()
    if primary_row is None or offset_row is None:
        raise ValueError("Both transactions must exist.")
    if int(primary_row["user_id"]) != int(user_id) or int(offset_row["user_id"]) != int(user_id):
        raise ValueError("Transactions must belong to the current user.")

    cursor = conn.execute(
        "INSERT INTO cash_offsets (user_id, cash_txn_id, offset_txn_id) VALUES (?, ?, ?)",
        (user_id, primary_txn_id, offset_txn_id),
    )
    offset_id = int(cursor.lastrowid)
    conn.execute(
        "UPDATE transactions SET cash_offset_id = ?, is_excluded = 1 WHERE id IN (?, ?)",
        (offset_id, primary_txn_id, offset_txn_id),
    )
    conn.commit()
    return offset_id


def remove_offset_pair(conn: sqlite3.Connection, offset_id: int) -> None:
    """Remove an offset and restore both linked transactions."""

    row = conn.execute(
        "SELECT cash_txn_id, offset_txn_id FROM cash_offsets WHERE id = ?",
        (offset_id,),
    ).fetchone()
    if row is None:
        return

    conn.execute(
        "UPDATE transactions SET cash_offset_id = NULL, is_excluded = 0 WHERE id IN (?, ?)",
        (row["cash_txn_id"], row["offset_txn_id"]),
    )
    conn.execute("DELETE FROM cash_offsets WHERE id = ?", (offset_id,))
    conn.commit()

"""Cash withdrawal and offset helpers."""

from __future__ import annotations

import sqlite3


def record_cash_offset(
    conn: sqlite3.Connection,
    user_id: int,
    cash_txn_id: int,
    offset_txn_id: int,
) -> int:
    """
    Link a cash withdrawal to a cash spend or reimbursement.

    The cash offset keeps the transaction trail intact while letting the UI hide it from totals.
    """

    cash_row = conn.execute(
        "SELECT id, user_id FROM transactions WHERE id = ?",
        (cash_txn_id,),
    ).fetchone()
    offset_row = conn.execute(
        "SELECT id, user_id FROM transactions WHERE id = ?",
        (offset_txn_id,),
    ).fetchone()
    if cash_row is None or offset_row is None:
        raise ValueError("Both transactions must exist.")
    if int(cash_row["user_id"]) != int(user_id) or int(offset_row["user_id"]) != int(user_id):
        raise ValueError("Transactions must belong to the current user.")

    cursor = conn.execute(
        "INSERT INTO cash_offsets (user_id, cash_txn_id, offset_txn_id) VALUES (?, ?, ?)",
        (user_id, cash_txn_id, offset_txn_id),
    )
    cash_offset_id = int(cursor.lastrowid)
    conn.execute(
        "UPDATE transactions SET cash_offset_id = ?, is_excluded = 1 WHERE id IN (?, ?)",
        (cash_offset_id, cash_txn_id, offset_txn_id),
    )
    conn.commit()
    return cash_offset_id


def unlink_cash_offset(conn: sqlite3.Connection, cash_offset_id: int) -> None:
    """Remove a cash offset and restore the linked transactions."""

    row = conn.execute(
        "SELECT cash_txn_id, offset_txn_id FROM cash_offsets WHERE id = ?",
        (cash_offset_id,),
    ).fetchone()
    if row is None:
        return

    conn.execute(
        "UPDATE transactions SET cash_offset_id = NULL, is_excluded = 0 WHERE id IN (?, ?)",
        (row["cash_txn_id"], row["offset_txn_id"]),
    )
    conn.execute("DELETE FROM cash_offsets WHERE id = ?", (cash_offset_id,))
    conn.commit()

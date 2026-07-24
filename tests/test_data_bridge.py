"""Derived FIRE defaults remain aligned with current transaction classifications."""

from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path

from bridge.data_bridge import sync_fire_defaults
from shared.db import get_connection, init_db
from shared.fire_service import upsert_fire_spending_category


class DataBridgeTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        temporary.close()
        self.path = Path(temporary.name)
        self.conn = get_connection(self.path)
        init_db(self.conn)
        self.user_id = int(
            self.conn.execute(
                "INSERT INTO users (email, password_hash) VALUES ('bridge@test.local', 'unused')"
            ).lastrowid
        )
        self.conn.commit()

    def tearDown(self) -> None:
        self.conn.close()
        self.path.unlink(missing_ok=True)

    def _transaction(self, category: str, transaction_type: str, amount: float) -> None:
        self.conn.execute(
            """
            INSERT INTO transactions (
                user_id, date, description, amount, category, transaction_type, source
            )
            VALUES (?, ?, 'Synthetic row', ?, ?, ?, 'manual')
            """,
            (self.user_id, date.today().isoformat(), amount, category, transaction_type),
        )
        self.conn.commit()

    def test_sync_excludes_transfers_and_removes_stale_derived_categories(self) -> None:
        self._transaction("Uncategorized", "expense", -90)
        self._transaction("Transfer", "transfer_out", -3000)
        sync_fire_defaults(self.conn, self.user_id)

        self.conn.execute(
            """
            UPDATE transactions
            SET category = 'Groceries'
            WHERE user_id = ? AND category = 'Uncategorized'
            """,
            (self.user_id,),
        )
        self.conn.commit()
        sync_fire_defaults(self.conn, self.user_id)

        rows = self.conn.execute(
            """
            SELECT category, monthly_amount
            FROM fire_spending_baseline
            WHERE user_id = ?
            ORDER BY category
            """,
            (self.user_id,),
        ).fetchall()
        self.assertEqual(
            [(row["category"], row["monthly_amount"]) for row in rows],
            [("Groceries", 30.0)],
        )

    def test_sync_preserves_user_overrides_when_derived_category_disappears(self) -> None:
        upsert_fire_spending_category(
            self.conn,
            self.user_id,
            "Travel",
            500,
            is_override=True,
        )

        sync_fire_defaults(self.conn, self.user_id)

        saved = self.conn.execute(
            """
            SELECT monthly_amount, is_override
            FROM fire_spending_baseline
            WHERE user_id = ? AND category = 'Travel'
            """,
            (self.user_id,),
        ).fetchone()
        self.assertEqual(saved["monthly_amount"], 500)
        self.assertEqual(saved["is_override"], 1)


if __name__ == "__main__":
    unittest.main()

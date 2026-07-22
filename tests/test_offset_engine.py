"""Cash-offset lifecycle, totals, and user-isolation coverage."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from budget.importer import get_spending_summary
from budget.offset_engine import create_offset_pair, remove_offset_pair
from shared.db import get_connection, init_db


class OffsetEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary_database = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        temporary_database.close()
        self.database_path = Path(temporary_database.name)
        self.conn = get_connection(self.database_path)
        init_db(self.conn)
        self.user_id = self._create_user("offset-owner@test.local")
        self.other_user_id = self._create_user("offset-other@test.local")

    def tearDown(self) -> None:
        self.conn.close()
        self.database_path.unlink(missing_ok=True)

    def _create_user(self, email: str) -> int:
        return int(
            self.conn.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, 'unused')",
                (email,),
            ).lastrowid
        )

    def _create_transaction(self, user_id: int, description: str, amount: float) -> int:
        transaction_id = int(
            self.conn.execute(
                """
                INSERT INTO transactions (
                    user_id, date, description, amount, category, transaction_type, source
                )
                VALUES (?, '2026-07-01', ?, ?, 'Other', 'expense', 'manual')
                """,
                (user_id, description, amount),
            ).lastrowid
        )
        self.conn.commit()
        return transaction_id

    def test_create_and_remove_offset_preserves_totals_round_trip(self) -> None:
        self._create_transaction(self.user_id, "Groceries", -80.0)
        cash_id = self._create_transaction(self.user_id, "Cash withdrawal", -20.0)
        spend_id = self._create_transaction(self.user_id, "Cash purchase", -20.0)
        before = get_spending_summary(self.conn, self.user_id)

        offset_id = create_offset_pair(self.conn, self.user_id, cash_id, spend_id)
        linked_rows = self.conn.execute(
            "SELECT cash_offset_id, is_excluded FROM transactions WHERE id IN (?, ?) ORDER BY id",
            (cash_id, spend_id),
        ).fetchall()
        during = get_spending_summary(self.conn, self.user_id)

        self.assertTrue(all(row["cash_offset_id"] == offset_id for row in linked_rows))
        self.assertTrue(all(row["is_excluded"] == 1 for row in linked_rows))
        self.assertEqual(before.spending_total, 120.0)
        self.assertEqual(during.spending_total, 80.0)

        self.assertTrue(remove_offset_pair(self.conn, self.user_id, offset_id))
        restored_rows = self.conn.execute(
            "SELECT cash_offset_id, is_excluded FROM transactions WHERE id IN (?, ?) ORDER BY id",
            (cash_id, spend_id),
        ).fetchall()
        after = get_spending_summary(self.conn, self.user_id)

        self.assertTrue(all(row["cash_offset_id"] is None for row in restored_rows))
        self.assertTrue(all(row["is_excluded"] == 0 for row in restored_rows))
        self.assertEqual(after.spending_total, before.spending_total)
        self.assertEqual(
            self.conn.execute("SELECT COUNT(*) FROM cash_offsets WHERE id = ?", (offset_id,)).fetchone()[0],
            0,
        )

    def test_create_rejects_transactions_owned_by_another_user(self) -> None:
        owner_transaction = self._create_transaction(self.user_id, "Owner cash", -20.0)
        other_transaction = self._create_transaction(self.other_user_id, "Other cash", -20.0)

        with self.assertRaisesRegex(ValueError, "current user"):
            create_offset_pair(self.conn, self.user_id, owner_transaction, other_transaction)

        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM cash_offsets").fetchone()[0], 0)

    def test_remove_cannot_unlink_another_users_offset(self) -> None:
        first_id = self._create_transaction(self.user_id, "First", -20.0)
        second_id = self._create_transaction(self.user_id, "Second", -20.0)
        offset_id = create_offset_pair(self.conn, self.user_id, first_id, second_id)

        self.assertFalse(remove_offset_pair(self.conn, self.other_user_id, offset_id))
        linked_count = self.conn.execute(
            "SELECT COUNT(*) FROM transactions WHERE cash_offset_id = ? AND is_excluded = 1",
            (offset_id,),
        ).fetchone()[0]
        self.assertEqual(linked_count, 2)
        self.assertEqual(
            self.conn.execute("SELECT COUNT(*) FROM cash_offsets WHERE id = ?", (offset_id,)).fetchone()[0],
            1,
        )

    def test_transaction_cannot_be_reused_or_paired_with_itself(self) -> None:
        first_id = self._create_transaction(self.user_id, "First", -20.0)
        second_id = self._create_transaction(self.user_id, "Second", -20.0)
        third_id = self._create_transaction(self.user_id, "Third", -20.0)

        with self.assertRaisesRegex(ValueError, "two different"):
            create_offset_pair(self.conn, self.user_id, first_id, first_id)

        create_offset_pair(self.conn, self.user_id, first_id, second_id)
        with self.assertRaisesRegex(ValueError, "only one offset"):
            create_offset_pair(self.conn, self.user_id, first_id, third_id)


if __name__ == "__main__":
    unittest.main()

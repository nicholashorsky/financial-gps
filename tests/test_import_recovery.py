"""Import batch, duplicate, and recovery behavior."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from budget.importer import import_csv_transactions, list_import_batches, undo_import_batch
from shared.db import get_connection, init_db


class ImportRecoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        temp_db = tempfile.NamedTemporaryFile(delete=False)
        temp_db.close()
        self.db_path = Path(temp_db.name)
        self.conn = get_connection(self.db_path)
        init_db(self.conn)
        self.user_id = self._user("owner@test.local")
        self.other_user_id = self._user("other@test.local")
        self.csv = "date,description,amount\n2026-07-01,Coffee,-5.00\n2026-07-02,Payroll,1000.00\n"

    def tearDown(self) -> None:
        self.conn.close()
        self.db_path.unlink(missing_ok=True)

    def _user(self, email: str) -> int:
        return int(
            self.conn.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, 'unused')",
                (email,),
            ).lastrowid
        )

    def _transaction_count(self) -> int:
        return int(
            self.conn.execute(
                "SELECT COUNT(*) FROM transactions WHERE user_id = ?",
                (self.user_id,),
            ).fetchone()[0]
        )

    def test_reimport_is_recorded_and_undo_removes_only_new_rows(self) -> None:
        first, _ = import_csv_transactions(self.conn, self.user_id, self.csv, filename="bank.csv")
        second, _ = import_csv_transactions(self.conn, self.user_id, self.csv, filename="bank.csv")

        self.assertEqual((first.imported, first.skipped_duplicates), (2, 0))
        self.assertEqual((second.imported, second.skipped_duplicates), (0, 2))
        self.assertEqual(self._transaction_count(), 2)
        self.assertEqual(len(list_import_batches(self.conn, self.user_id)), 2)

        self.assertEqual(undo_import_batch(self.conn, self.user_id, int(second.batch_id)), 0)
        self.assertEqual(self._transaction_count(), 2)
        self.assertEqual(undo_import_batch(self.conn, self.user_id, int(first.batch_id)), 2)
        self.assertEqual(self._transaction_count(), 0)

    def test_other_user_cannot_undo_batch(self) -> None:
        result, _ = import_csv_transactions(self.conn, self.user_id, self.csv, filename="private.csv")

        deleted = undo_import_batch(self.conn, self.other_user_id, int(result.batch_id))

        self.assertEqual(deleted, 0)
        self.assertEqual(self._transaction_count(), 2)

    def test_updated_export_imports_only_new_transactions(self) -> None:
        import_csv_transactions(self.conn, self.user_id, self.csv, filename="bank.csv")
        updated_csv = self.csv + "2026-07-03,Groceries,-75.00\n"

        result, _ = import_csv_transactions(self.conn, self.user_id, updated_csv, filename="bank-updated.csv")

        self.assertEqual((result.imported, result.skipped_duplicates), (1, 2))
        self.assertEqual(self._transaction_count(), 3)

    def test_empty_file_does_not_create_an_import_batch(self) -> None:
        result, transactions = import_csv_transactions(self.conn, self.user_id, b"", filename="empty.csv")

        self.assertEqual(result.imported, 0)
        self.assertEqual(transactions, [])
        self.assertIsNone(result.batch_id)
        self.assertTrue(any("nothing was imported" in warning.lower() for warning in result.warnings))
        self.assertEqual(list_import_batches(self.conn, self.user_id), [])

    def test_import_result_reports_invalid_rows(self) -> None:
        csv = (
            "date,description,amount\n"
            "not-a-date,Coffee,-5.00\n"
            "2026-07-02,Payroll,1000.00\n"
        )

        result, transactions = import_csv_transactions(self.conn, self.user_id, csv, filename="mixed.csv")

        self.assertEqual(result.imported, 1)
        self.assertEqual(result.skipped_invalid, 1)
        self.assertEqual(len(transactions), 1)
        self.assertTrue(any("invalid row" in warning.lower() for warning in result.warnings))


if __name__ == "__main__":
    unittest.main()

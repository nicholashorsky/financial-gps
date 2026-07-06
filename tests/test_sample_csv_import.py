"""Regression coverage for the checked-in beta transaction sample."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from bridge.bridge_status import get_bridge_status
from budget.csv_parser import parse_csv
from budget.importer import get_spending_summary, import_csv_transactions
from shared.db import get_connection, init_db


SAMPLE_CSV = Path(__file__).resolve().parent.parent / "csv samples" / "RBC SAMPLE CSV.csv"


class SampleCSVImportTests(unittest.TestCase):
    def test_rbc_sample_import_exercises_accounts_transfers_and_bridge(self) -> None:
        temp_db = tempfile.NamedTemporaryFile(delete=False)
        temp_db.close()
        db_path = Path(temp_db.name)

        try:
            conn = get_connection(db_path)
            try:
                init_db(conn)
                user_id = conn.execute(
                    """
                    INSERT INTO users (email, password_hash, name)
                    VALUES ('sample@test.local', 'unused', 'Sample Tester')
                    """
                ).lastrowid
                conn.commit()

                sample_content = SAMPLE_CSV.read_text(encoding="utf-8-sig")
                parsed = parse_csv(sample_content)

                self.assertEqual(parsed.format_name, "rbc_multi")
                self.assertGreaterEqual(len(parsed.transactions), 100)
                self.assertEqual(
                    {account.account_type for account in parsed.accounts},
                    {"chequing", "credit", "savings"},
                )

                result, categorized = import_csv_transactions(conn, int(user_id), sample_content)
                summary = get_spending_summary(conn, int(user_id))
                bridge_status = get_bridge_status(conn, int(user_id))

                self.assertEqual(result.imported, len(categorized))
                self.assertGreaterEqual(result.imported, 100)
                self.assertGreaterEqual(result.transfers_matched, 5)
                self.assertEqual(summary.account_count, 4)
                self.assertEqual(summary.transaction_count, result.imported)
                self.assertGreater(summary.spending_total, 0)
                self.assertGreater(summary.income_total, 0)
                self.assertGreaterEqual(bridge_status["income_rows"], 1)
                self.assertGreaterEqual(bridge_status["spending_rows"], 1)
            finally:
                conn.close()
        finally:
            db_path.unlink(missing_ok=True)

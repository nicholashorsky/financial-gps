"""Synthetic-beta notice, deletion, and upload-retention coverage."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import shared.db as db_module
from auth import delete_user_account
from budget.importer import import_csv_transactions
from shared.beta_policy import SYNTHETIC_DATA_NOTICE
from shared.db import get_connection, init_db


class BetaPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary_database = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        temporary_database.close()
        self.database_path = Path(temporary_database.name)
        self.original_database_path = db_module.DB_PATH
        db_module.DB_PATH = self.database_path
        self.conn = get_connection(self.database_path)
        init_db(self.conn)

    def tearDown(self) -> None:
        self.conn.close()
        db_module.DB_PATH = self.original_database_path
        self.database_path.unlink(missing_ok=True)

    def _create_user(self, email: str) -> int:
        user_id = int(
            self.conn.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, 'unused')",
                (email,),
            ).lastrowid
        )
        self.conn.commit()
        return user_id

    def test_shared_notice_states_synthetic_only_and_no_recovery_guarantee(self) -> None:
        self.assertIn("Synthetic sample data only", SYNTHETIC_DATA_NOTICE)
        self.assertIn("Do not enter or upload real", SYNTHETIC_DATA_NOTICE)
        self.assertIn("no backup or recovery guarantee", SYNTHETIC_DATA_NOTICE)

    def test_account_deletion_cascades_only_for_selected_user(self) -> None:
        user_id = self._create_user("delete@test.local")
        other_user_id = self._create_user("keep@test.local")
        for owner_id, suffix in ((user_id, "delete"), (other_user_id, "keep")):
            account_id = int(
                self.conn.execute(
                    "INSERT INTO accounts (user_id, name, type) VALUES (?, ?, 'chequing')",
                    (owner_id, suffix),
                ).lastrowid
            )
            self.conn.execute(
                """
                INSERT INTO transactions (user_id, account_id, date, description, amount)
                VALUES (?, ?, '2026-07-01', ?, -10)
                """,
                (owner_id, account_id, suffix),
            )
            self.conn.execute(
                "INSERT INTO goals (user_id, name, target_amount) VALUES (?, ?, 100)",
                (owner_id, suffix),
            )
        self.conn.commit()

        self.assertTrue(delete_user_account(user_id))

        self.assertEqual(
            self.conn.execute("SELECT COUNT(*) FROM users WHERE id = ?", (user_id,)).fetchone()[0],
            0,
        )
        for table in ("accounts", "transactions", "goals"):
            self.assertEqual(
                self.conn.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE user_id = ?",
                    (user_id,),
                ).fetchone()[0],
                0,
            )
            self.assertGreater(
                self.conn.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE user_id = ?",
                    (other_user_id,),
                ).fetchone()[0],
                0,
            )

    def test_import_stores_filename_metadata_but_not_source_payload(self) -> None:
        user_id = self._create_user("import@test.local")
        csv_content = "date,description,amount\n2026-07-01,Synthetic Coffee,-5.00\n"

        result, _ = import_csv_transactions(
            self.conn,
            user_id,
            csv_content,
            filename="synthetic.csv",
        )

        columns = {
            row["name"]
            for row in self.conn.execute("PRAGMA table_info(import_batches)").fetchall()
        }
        batch = self.conn.execute(
            "SELECT * FROM import_batches WHERE id = ?",
            (result.batch_id,),
        ).fetchone()
        self.assertNotIn("content", columns)
        self.assertNotIn("payload", columns)
        self.assertNotIn("file_data", columns)
        self.assertEqual(batch["filename"], "synthetic.csv")
        self.assertNotIn(csv_content, [str(value) for value in tuple(batch)])


if __name__ == "__main__":
    unittest.main()

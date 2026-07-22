"""CPP benefit override persistence and user-isolation coverage."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from shared.db import get_connection, init_db
from shared.fire_service import (
    get_data_quality_warnings,
    list_benefit_enrollments,
    upsert_benefit_enrollment,
)


class FireBenefitTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary_database = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        temporary_database.close()
        self.database_path = Path(temporary_database.name)
        self.conn = get_connection(self.database_path)
        init_db(self.conn)

    def tearDown(self) -> None:
        self.conn.close()
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

    def test_manual_cpp_estimate_is_saved_per_user_and_resolves_warning(self) -> None:
        user_id = self._create_user("cpp@test.local")
        other_user_id = self._create_user("other@test.local")

        upsert_benefit_enrollment(
            self.conn,
            user_id,
            "CPP",
            70,
            estimated_monthly_amount=1420,
            source="manual",
            cpp_estimate_at_65=1000,
        )

        saved = list_benefit_enrollments(self.conn, user_id)
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0]["cpp_estimate_at_65"], 1000)
        self.assertEqual(saved[0]["estimated_monthly_amount"], 1420)
        self.assertEqual(saved[0]["source"], "manual")
        self.assertEqual(list_benefit_enrollments(self.conn, other_user_id), [])
        self.assertNotIn(
            "cpp_missing",
            {warning.code for warning in get_data_quality_warnings(self.conn, user_id)},
        )


if __name__ == "__main__":
    unittest.main()

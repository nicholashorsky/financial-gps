"""Plan revisions, isolation, snapshots, and engine adapter coverage."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from shared.db import get_connection, init_db
from shared.fire_service import save_fire_profile, upsert_fire_income_source
from shared.planning_service import (
    archive_plan,
    create_plan,
    duplicate_plan,
    get_plan,
    list_plans,
    project_plan,
    refresh_plan_sections,
    rename_plan,
    save_plan_revision,
    set_active_plan,
)


class PlanningServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        temporary.close()
        self.path = Path(temporary.name)
        self.conn = get_connection(self.path)
        init_db(self.conn)
        self.user_id = self._user("planner@test.local")
        self.other_user_id = self._user("other@test.local")

    def tearDown(self) -> None:
        self.conn.close()
        self.path.unlink(missing_ok=True)

    def _user(self, email: str) -> int:
        user_id = int(
            self.conn.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, 'unused')",
                (email,),
            ).lastrowid
        )
        self.conn.commit()
        return user_id

    def test_plan_revision_is_immutable_and_user_isolated(self) -> None:
        plan = create_plan(self.conn, self.user_id, "Base", from_current_finances=False)
        payload = plan["payload"]
        payload["profile"]["province"] = "ON"
        save_plan_revision(self.conn, self.user_id, plan["id"], payload)

        revisions = self.conn.execute(
            "SELECT revision_number, payload FROM planning_plan_revisions WHERE plan_id = ? ORDER BY revision_number",
            (plan["id"],),
        ).fetchall()
        self.assertEqual([row["revision_number"] for row in revisions], [1, 2])
        self.assertIsNone(__import__("json").loads(revisions[0]["payload"])["profile"]["province"])
        self.assertEqual(list_plans(self.conn, self.other_user_id), [])
        with self.assertRaises(ValueError):
            get_plan(self.conn, self.other_user_id, plan["id"])

    def test_duplicate_is_independent_and_selective_refresh_preserves_edits(self) -> None:
        save_fire_profile(self.conn, self.user_id, province="ON", date_of_birth="1980-01-01")
        upsert_fire_income_source(self.conn, self.user_id, "employment", 80000, is_override=True)
        plan = create_plan(self.conn, self.user_id, "Current")
        duplicate = duplicate_plan(self.conn, self.user_id, plan["id"], "Alternative")

        edited = duplicate["payload"]
        edited["profile"]["target_retire_year"] = 2040
        save_plan_revision(self.conn, self.user_id, duplicate["id"], edited)
        upsert_fire_income_source(self.conn, self.user_id, "employment", 90000, is_override=True)
        refresh_plan_sections(self.conn, self.user_id, duplicate["id"], {"income"})

        refreshed = get_plan(self.conn, self.user_id, duplicate["id"])
        self.assertEqual(refreshed["payload"]["income"][0]["annual_amount"], 90000)
        self.assertEqual(refreshed["payload"]["profile"]["target_retire_year"], 2040)
        self.assertEqual(get_plan(self.conn, self.user_id, plan["id"])["payload"]["income"][0]["annual_amount"], 80000)

    def test_plan_payload_projects_with_valid_profile(self) -> None:
        plan = create_plan(self.conn, self.user_id, "Projection", from_current_finances=False)
        payload = plan["payload"]
        payload["profile"].update({"province": "ON", "date_of_birth": "1980-01-01"})
        payload["income"] = [{"source_type": "employment", "annual_amount": 80000}]
        payload["spending"] = [{"category": "Living", "monthly_amount": 3000}]
        payload["accounts"] = [{"account_type": "TFSA", "current_balance": 100000}]

        projection = project_plan(payload)

        self.assertEqual(len(projection), 40)
        self.assertGreater(projection[0].net_worth, 0)

    def test_plan_lifecycle_preserves_revisions_and_selects_replacement(self) -> None:
        base = create_plan(self.conn, self.user_id, "Base", from_current_finances=False)
        alternative = duplicate_plan(self.conn, self.user_id, base["id"], "Alternative")
        rename_plan(self.conn, self.user_id, alternative["id"], "Retire Earlier")
        set_active_plan(self.conn, self.user_id, alternative["id"])

        archive_plan(self.conn, self.user_id, alternative["id"])

        visible = list_plans(self.conn, self.user_id)
        self.assertEqual([plan["name"] for plan in visible], ["Base"])
        self.assertEqual(visible[0]["is_active"], 1)
        archived = get_plan(self.conn, self.user_id, alternative["id"])
        self.assertEqual(archived["status"], "archived")
        revision_count = self.conn.execute(
            "SELECT COUNT(*) FROM planning_plan_revisions WHERE plan_id = ?",
            (alternative["id"],),
        ).fetchone()[0]
        self.assertEqual(revision_count, 2)

    def test_schema_upgrade_adds_plan_tables_without_changing_legacy_rows(self) -> None:
        legacy_user_id = self._user("legacy@test.local")
        self.conn.execute("DROP TABLE planning_plan_revisions")
        self.conn.execute("DROP TABLE planning_plans")
        self.conn.commit()

        init_db(self.conn)

        saved = self.conn.execute(
            "SELECT email FROM users WHERE id = ?",
            (legacy_user_id,),
        ).fetchone()
        self.assertEqual(saved["email"], "legacy@test.local")
        table_names = {
            row["name"]
            for row in self.conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        self.assertIn("planning_plans", table_names)
        self.assertIn("planning_plan_revisions", table_names)


if __name__ == "__main__":
    unittest.main()

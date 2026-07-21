"""User-isolated category and categorization-rule preferences."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from budget.categorizer import (
    CATEGORIES,
    add_user_category,
    add_user_rule,
    categorize_description,
    count_rule_matches,
    get_all_rules,
    get_user_categories,
    rename_user_category,
    seed_system_rules,
    set_category_enabled,
    set_rule_enabled,
    update_user_rule,
)
from shared.db import get_connection, init_db


class CategoryPreferenceTests(unittest.TestCase):
    def setUp(self) -> None:
        temp_db = tempfile.NamedTemporaryFile(delete=False)
        temp_db.close()
        self.db_path = Path(temp_db.name)
        self.conn = get_connection(self.db_path)
        init_db(self.conn)
        self.user_id = self._user("rules-one@test.local")
        self.other_user_id = self._user("rules-two@test.local")

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

    def test_default_and_custom_categories_are_user_isolated(self) -> None:
        self.assertEqual(set(get_user_categories(self.conn, self.user_id)), set(CATEGORIES))
        add_user_category(self.conn, self.user_id, "Pets")

        self.assertIn("Pets", get_user_categories(self.conn, self.user_id))
        self.assertNotIn("Pets", get_user_categories(self.conn, self.other_user_id))

    def test_disabling_system_rule_affects_only_current_user(self) -> None:
        seed_system_rules(self.conn, self.user_id)
        seed_system_rules(self.conn, self.other_user_id)
        rule_id = int(
            self.conn.execute(
                "SELECT id FROM category_rules WHERE user_id = ? AND keyword = 'rent' AND source = 'system'",
                (self.user_id,),
            ).fetchone()[0]
        )
        set_rule_enabled(self.conn, rule_id, self.user_id, False)

        own_category, _ = categorize_description("Monthly rent", -1200, get_all_rules(self.conn, self.user_id))
        other_category, _ = categorize_description(
            "Monthly rent", -1200, get_all_rules(self.conn, self.other_user_id)
        )

        self.assertEqual(own_category, "Uncategorized")
        self.assertEqual(other_category, "Housing")

    def test_user_rule_can_be_edited_but_not_by_another_user(self) -> None:
        rule_id = add_user_rule(self.conn, self.user_id, "pet store", "Shopping", 50)

        self.assertFalse(update_user_rule(self.conn, rule_id, self.other_user_id, "pet store", "Other", 80))
        self.assertTrue(update_user_rule(self.conn, rule_id, self.user_id, "pet store", "Other", 80))
        category, _ = categorize_description("Pet Store Guelph", -25, get_all_rules(self.conn, self.user_id))
        self.assertEqual(category, "Other")

    def test_disabled_category_prevents_its_rules_from_running(self) -> None:
        category_id = add_user_category(self.conn, self.user_id, "Pets")
        add_user_rule(self.conn, self.user_id, "veterinary", "Pets", 90)
        set_category_enabled(self.conn, self.user_id, category_id, False)

        category, _ = categorize_description("Veterinary clinic", -100, get_all_rules(self.conn, self.user_id))

        self.assertEqual(category, "Uncategorized")

    def test_in_use_custom_category_cannot_be_renamed(self) -> None:
        category_id = add_user_category(self.conn, self.user_id, "Pets")
        account_id = int(
            self.conn.execute(
                "INSERT INTO accounts (user_id, name, type) VALUES (?, 'Visa', 'credit')",
                (self.user_id,),
            ).lastrowid
        )
        self.conn.execute(
            """
            INSERT INTO transactions (user_id, account_id, date, description, amount, category)
            VALUES (?, ?, '2026-07-01', 'Vet', -100, 'Pets')
            """,
            (self.user_id, account_id),
        )
        self.conn.commit()

        with self.assertRaisesRegex(ValueError, "in use"):
            rename_user_category(self.conn, self.user_id, category_id, "Animals")

        self.assertEqual(count_rule_matches(self.conn, self.user_id, "vet"), 1)
        self.assertEqual(count_rule_matches(self.conn, self.other_user_id, "vet"), 0)


if __name__ == "__main__":
    unittest.main()

"""Focused tests for transaction-review progress and rule previews."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pages.spending import (
    _review_session_progress,
    _review_transactions,
    _rule_keyword_from_description,
    _rule_preview,
)
from shared.db import get_connection, init_db


class ReviewProgressTests(unittest.TestCase):
    def test_progress_distinguishes_completed_remaining_and_skipped(self) -> None:
        progress = _review_session_progress(
            session_ids={1, 2, 3, 4},
            current_ids={2, 3, 4},
            skipped_ids={4, 99},
        )

        self.assertEqual(
            progress,
            {"total": 4, "completed": 1, "remaining": 2, "skipped": 1},
        )


class RuleKeywordTests(unittest.TestCase):
    def test_lcbo_reference_and_location_noise_is_removed(self) -> None:
        keyword = _rule_keyword_from_description("LCBO/RAO #0495 GUELPH ON")

        self.assertEqual(keyword, "lcbo")

    def test_transfer_label_prefix_is_removed_from_match_text(self) -> None:
        keyword = _rule_keyword_from_description("Transfer — WWW TRANSFER - 4793")

        self.assertEqual(keyword, "www transfer")


class RulePreviewTests(unittest.TestCase):
    def setUp(self) -> None:
        temp_db = tempfile.NamedTemporaryFile(delete=False)
        temp_db.close()
        self.db_path = Path(temp_db.name)
        self.conn = get_connection(self.db_path)
        init_db(self.conn)

        self.user_one = self._create_user("one@test.local")
        self.user_two = self._create_user("two@test.local")
        self.account_one = self._create_account(self.user_one, "User One Visa")
        self.account_two = self._create_account(self.user_two, "User Two Visa")

    def tearDown(self) -> None:
        self.conn.close()
        self.db_path.unlink(missing_ok=True)

    def _create_user(self, email: str) -> int:
        cursor = self.conn.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, 'unused')",
            (email,),
        )
        return int(cursor.lastrowid)

    def _create_account(self, user_id: int, name: str) -> int:
        cursor = self.conn.execute(
            "INSERT INTO accounts (user_id, name, type) VALUES (?, ?, 'credit')",
            (user_id, name),
        )
        return int(cursor.lastrowid)

    def _create_transaction(
        self,
        user_id: int,
        account_id: int,
        description: str,
        category: str,
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO transactions (
                user_id, account_id, date, description, amount, category,
                transaction_type, source
            )
            VALUES (?, ?, '2026-07-01', ?, -10, ?, 'expense', 'csv_import')
            """,
            (user_id, account_id, description, category),
        )
        self.conn.commit()

    def test_preview_only_counts_uncategorized_matches_for_current_user(self) -> None:
        self._create_transaction(self.user_one, self.account_one, "Spotify June", "Uncategorized")
        self._create_transaction(self.user_one, self.account_one, "Spotify May", "Entertainment")
        self._create_transaction(self.user_two, self.account_two, "Spotify June", "Uncategorized")

        preview = _rule_preview(self.conn, self.user_one, "spotify")

        self.assertEqual(preview["count"], 1)
        self.assertEqual(preview["accounts"], ["User One Visa"])

    def test_empty_keyword_matches_nothing(self) -> None:
        self._create_transaction(self.user_one, self.account_one, "Spotify June", "Uncategorized")

        preview = _rule_preview(self.conn, self.user_one, "  ")

        self.assertEqual(preview, {"count": 0, "accounts": []})

    def test_review_queue_is_not_limited_to_fifty_transactions(self) -> None:
        for index in range(55):
            self._create_transaction(
                self.user_one,
                self.account_one,
                f"Merchant {index}",
                "Uncategorized",
            )

        transactions = _review_transactions(self.conn, self.user_one)

        self.assertEqual(len(transactions), 55)

    def test_transfer_rule_keyword_matches_both_reference_variants(self) -> None:
        self._create_transaction(
            self.user_one,
            self.account_one,
            "Transfer — WWW TRANSFER - 4793",
            "Uncategorized",
        )
        self._create_transaction(
            self.user_one,
            self.account_one,
            "Transfer — WWW TRANSFER - 4857",
            "Uncategorized",
        )

        keyword = _rule_keyword_from_description("Transfer — WWW TRANSFER - 4793")
        preview = _rule_preview(self.conn, self.user_one, keyword)

        self.assertEqual(preview["count"], 2)

    def test_preview_matches_normalized_keyword_across_description_punctuation(self) -> None:
        self._create_transaction(
            self.user_one,
            self.account_one,
            "PAYPAL *MICROSOFT 4029357733 ON",
            "Uncategorized",
        )

        preview = _rule_preview(self.conn, self.user_one, "paypal microsoft")

        self.assertEqual(preview["count"], 1)


if __name__ == "__main__":
    unittest.main()

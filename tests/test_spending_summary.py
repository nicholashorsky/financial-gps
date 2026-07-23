"""Spending summary financial-correctness tests."""

from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from budget.importer import get_spending_summary
from pages.spending import _overview_period_range, _period_overview, _render_category_chart
from shared.db import get_connection, init_db


class SpendingSummaryTests(unittest.TestCase):
    def test_category_chart_keeps_labels_off_donut_slices(self) -> None:
        summary = SimpleNamespace(
            spending_by_category=[
                {"category": "Groceries", "total": 80.0},
                {"category": "Dining", "total": 40.0},
            ]
        )

        with patch("pages.spending.st.plotly_chart") as plotly_chart:
            _render_category_chart(summary)

        figure = plotly_chart.call_args.args[0]
        self.assertEqual(figure.data[0].textinfo, "none")
        self.assertIn("%{label}", figure.data[0].hovertemplate)

    def test_last_thirty_days_has_equal_previous_comparison_period(self) -> None:
        self.assertEqual(
            _overview_period_range("Last 30 days", date(2026, 7, 20)),
            ("2026-06-21", "2026-07-21", "2026-05-22", "2026-06-21"),
        )

    def test_transfer_categories_are_visible_but_not_counted_as_spending_or_income(self) -> None:
        temp_db = tempfile.NamedTemporaryFile(delete=False)
        temp_db.close()
        db_path = Path(temp_db.name)
        conn = get_connection(db_path)
        try:
            init_db(conn)
            user_id = int(
                conn.execute(
                    "INSERT INTO users (email, password_hash) VALUES ('summary@test.local', 'unused')"
                ).lastrowid
            )
            account_id = int(
                conn.execute(
                    "INSERT INTO accounts (user_id, name, type) VALUES (?, 'Chequing', 'chequing')",
                    (user_id,),
                ).lastrowid
            )
            rows = [
                ("Groceries", "expense", -80.0),
                ("Income", "income", 1000.0),
                ("Transfer", "transfer_out", -250.0),
                ("Transfer", "transfer_in", 250.0),
            ]
            for category, transaction_type, amount in rows:
                conn.execute(
                    """
                    INSERT INTO transactions (
                        user_id, account_id, date, description, amount, category,
                        transaction_type, is_excluded, source
                    )
                    VALUES (?, ?, '2026-07-01', ?, ?, ?, ?, 0, 'manual')
                    """,
                    (user_id, account_id, category, amount, category, transaction_type),
                )
            conn.commit()

            summary = get_spending_summary(conn, user_id)

            self.assertEqual(summary.spending_total, 80.0)
            self.assertEqual(summary.income_total, 1000.0)
            self.assertEqual([row["category"] for row in summary.spending_by_category], ["Groceries"])
            self.assertEqual(len(summary.recent_transactions), 4)
            overview = _period_overview(conn, user_id, "Last 30 days", date(2026, 7, 20))
            self.assertEqual(overview["spending"], 80.0)
            self.assertEqual(overview["income"], 1000.0)
            self.assertEqual([row["category"] for row in overview["categories"]], ["Groceries"])
        finally:
            conn.close()
            db_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()

"""Regression coverage for basic forecast input and projection states."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pages.forecast import (
    _annual_projection,
    _band_contributions,
    _forecast_state,
    _monthly_cash_flow,
)
from shared.db import get_connection, init_db


class ForecastTests(unittest.TestCase):
    def test_empty_forecast_requires_setup(self) -> None:
        self.assertEqual(_forecast_state(0.0, 0), "needs_setup")
        self.assertEqual(_forecast_state(1000.0, 0), "configured")
        self.assertEqual(_forecast_state(0.0, 1), "configured")

    def test_configured_positive_projection_preserves_band_assumptions(self) -> None:
        contributions = _band_contributions(1000.0, income_growth=0.03, inflation=0.025)

        self.assertAlmostEqual(contributions["Conservative"], 11700.0)
        self.assertAlmostEqual(contributions["Expected"], 12000.0 * (1.03**0.5))
        self.assertAlmostEqual(contributions["Optimistic"], 12360.0)

    def test_negative_cash_flow_is_applied_to_every_band(self) -> None:
        contributions = _band_contributions(-500.0, income_growth=0.03, inflation=0.025)

        self.assertLess(contributions["Conservative"], contributions["Expected"])
        self.assertLess(contributions["Expected"], contributions["Optimistic"])
        for contribution in contributions.values():
            self.assertLess(contribution, 0)
            self.assertLess(_annual_projection(10000.0, contribution, 1, 0.0)[0], 10000.0)

    def test_cash_flow_averages_months_and_excludes_transfers(self) -> None:
        temporary_database = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        temporary_database.close()
        database_path = Path(temporary_database.name)
        conn = get_connection(database_path)
        try:
            init_db(conn)
            user_id = int(
                conn.execute(
                    "INSERT INTO users (email, password_hash) VALUES ('forecast@test.local', 'unused')"
                ).lastrowid
            )
            rows = [
                ("2026-05-01", "Pay", 3000.0, "Income", "income"),
                ("2026-05-02", "Expenses", -2000.0, "Housing", "expense"),
                ("2026-06-01", "Pay", 3200.0, "Income", "income"),
                ("2026-06-02", "Expenses", -1800.0, "Housing", "expense"),
                ("2026-06-03", "Internal transfer", -500.0, "Other", "transfer_out"),
            ]
            for transaction_date, description, amount, category, transaction_type in rows:
                conn.execute(
                    """
                    INSERT INTO transactions (
                        user_id, date, description, amount, category, transaction_type, source
                    )
                    VALUES (?, ?, ?, ?, ?, ?, 'manual')
                    """,
                    (user_id, transaction_date, description, amount, category, transaction_type),
                )
            conn.commit()

            monthly_cash_flow, observed_months = _monthly_cash_flow(conn, user_id)

            self.assertEqual(observed_months, 2)
            self.assertEqual(monthly_cash_flow, 1200.0)
        finally:
            conn.close()
            database_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()

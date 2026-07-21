"""Shared presentation formatting tests."""

from __future__ import annotations

import unittest
from datetime import date

from shared.formatting import format_currency, format_date, format_month


class FormattingTests(unittest.TestCase):
    def test_currency_signs_and_precision_are_consistent(self) -> None:
        self.assertEqual(format_currency(-1234.5), "-$1,234.50")
        self.assertEqual(format_currency(1234.5, show_plus=True), "+$1,234.50")
        self.assertEqual(format_currency(None), "$0.00")

    def test_dates_are_readable_and_have_a_fallback(self) -> None:
        self.assertEqual(format_date(date(2026, 7, 21)), "Jul 21, 2026")
        self.assertEqual(format_date("2026-07-01"), "Jul 1, 2026")
        self.assertEqual(format_date(None), "Unknown date")

    def test_month_keys_are_formatted_as_categorical_labels(self) -> None:
        self.assertEqual(format_month("2026-04"), "Apr 2026")


if __name__ == "__main__":
    unittest.main()

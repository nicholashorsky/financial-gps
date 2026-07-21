"""CSV validation and error-reporting tests."""

from __future__ import annotations

import unittest

from budget.csv_parser import parse_csv


class CSVValidationTests(unittest.TestCase):
    def test_invalid_date_is_reported(self) -> None:
        result = parse_csv("date,description,amount\nnot-a-date,Coffee,-5\n")

        self.assertEqual(result.transactions, [])
        self.assertEqual(result.skipped_invalid, 1)
        self.assertTrue(any("Skipped 1 invalid row" in warning for warning in result.warnings))

    def test_invalid_amount_is_reported(self) -> None:
        result = parse_csv("date,description,amount\n2026-07-01,Coffee,banana\n")

        self.assertEqual(result.transactions, [])
        self.assertEqual(result.skipped_invalid, 1)
        self.assertTrue(any("valid date, description, and amount" in warning for warning in result.warnings))

    def test_unknown_columns_require_mapping(self) -> None:
        result = parse_csv("not,a,recognized,file\n1,2,3,4\n")

        self.assertTrue(result.needs_column_mapping)
        self.assertEqual(result.format_name, "unknown")


if __name__ == "__main__":
    unittest.main()

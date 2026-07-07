"""Categorization behavior that protects review workflow UX."""

from __future__ import annotations

import unittest

from budget.categorizer import categorize_description


class CategorizerTests(unittest.TestCase):
    def test_unknown_transaction_requires_review(self) -> None:
        category, transaction_type = categorize_description("Mystery Vendor 123", -42.0)

        self.assertEqual(category, "Uncategorized")
        self.assertEqual(transaction_type, "expense")


if __name__ == "__main__":
    unittest.main()

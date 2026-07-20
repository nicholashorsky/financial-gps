"""Categorization behavior that protects review workflow UX."""

from __future__ import annotations

import unittest

from budget.categorizer import CategoryRule, categorize_description, normalize_text


class CategorizerTests(unittest.TestCase):
    def test_unknown_transaction_requires_review(self) -> None:
        category, transaction_type = categorize_description("Mystery Vendor 123", -42.0)

        self.assertEqual(category, "Uncategorized")
        self.assertEqual(transaction_type, "expense")

    def test_rule_matching_ignores_punctuation_between_merchant_words(self) -> None:
        category, _ = categorize_description(
            "PAYPAL *MICROSOFT 4029357733 ON",
            -20.0,
            [CategoryRule("paypal microsoft", "Subscriptions", 100, "user")],
        )

        self.assertEqual(category, "Subscriptions")

    def test_normalize_text_collapses_symbols_and_whitespace(self) -> None:
        self.assertEqual(normalize_text("PAYPAL *MICROSOFT"), "paypal microsoft")


if __name__ == "__main__":
    unittest.main()

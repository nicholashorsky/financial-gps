from __future__ import annotations

import unittest

from fire_engine.calculators.federal_tax import calculate_federal_tax
from fire_engine.parameters.cra_2026 import CRA_2026


class FederalTaxTests(unittest.TestCase):
    def test_cra_regression_cases(self) -> None:
        for income, federal, _, _ in CRA_2026.regression_cases:
            result = calculate_federal_tax(income)
            self.assertEqual(result.federal_tax, federal)

    def test_positive_tax_for_mid_income(self) -> None:
        result = calculate_federal_tax(100000)
        self.assertGreater(result.federal_tax, 0)


if __name__ == "__main__":
    unittest.main()

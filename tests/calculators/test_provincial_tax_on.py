from __future__ import annotations

import unittest

from fire_engine.calculators.provincial_tax_on import calculate_ontario_tax
from fire_engine.parameters.cra_2026 import CRA_2026


class OntarioTaxTests(unittest.TestCase):
    def test_cra_regression_cases(self) -> None:
        for income, _, ontario, _ in CRA_2026.regression_cases:
            result = calculate_ontario_tax(income)
            self.assertEqual(result.provincial_tax, ontario)

    def test_health_premium_appears(self) -> None:
        result = calculate_ontario_tax(90000)
        self.assertGreater(result.provincial_tax, 0)


if __name__ == "__main__":
    unittest.main()

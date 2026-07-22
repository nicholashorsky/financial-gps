from __future__ import annotations

import unittest

from fire_engine.calculators.rrif_minimum import (
    calculate_rrif_minimum,
    rrif_prescribed_factor,
)


class RRIFMinimumTests(unittest.TestCase):
    def test_prescribed_factors_match_current_regulations(self) -> None:
        self.assertEqual(rrif_prescribed_factor(71), 0.0528)
        self.assertEqual(rrif_prescribed_factor(72), 0.0540)
        self.assertEqual(rrif_prescribed_factor(94), 0.1879)
        self.assertEqual(rrif_prescribed_factor(95), 0.20)

    def test_minimum_uses_opening_balance(self) -> None:
        result = calculate_rrif_minimum(72, 100000)

        self.assertEqual(result.factor, 0.0540)
        self.assertEqual(result.minimum_withdrawal, 5400.0)


if __name__ == "__main__":
    unittest.main()

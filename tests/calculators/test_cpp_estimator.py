from __future__ import annotations

import unittest

from fire_engine.calculators.cpp_estimator import estimate_cpp_monthly


class CPPEstimatorTests(unittest.TestCase):
    def test_cpp_deferral_increases_amount(self) -> None:
        at_65 = estimate_cpp_monthly(1.0, 65)
        at_70 = estimate_cpp_monthly(1.0, 70)
        self.assertGreater(at_70.monthly_amount, at_65.monthly_amount)

    def test_cpp_early_start_reduces_amount(self) -> None:
        at_60 = estimate_cpp_monthly(1.0, 60)
        at_65 = estimate_cpp_monthly(1.0, 65)
        self.assertLess(at_60.monthly_amount, at_65.monthly_amount)


if __name__ == "__main__":
    unittest.main()

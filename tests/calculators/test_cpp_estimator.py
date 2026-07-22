from __future__ import annotations

import unittest

from fire_engine.calculators.cpp_estimator import adjust_cpp_for_start_age, estimate_cpp_monthly


class CPPEstimatorTests(unittest.TestCase):
    def test_manual_age_65_estimate_adjusts_for_separate_start_age(self) -> None:
        self.assertEqual(adjust_cpp_for_start_age(1000, 60).monthly_amount, 640)
        self.assertEqual(adjust_cpp_for_start_age(1000, 65).monthly_amount, 1000)
        self.assertEqual(adjust_cpp_for_start_age(1000, 70).monthly_amount, 1420)

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

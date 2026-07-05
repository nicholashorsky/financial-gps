from __future__ import annotations

import unittest

from fire_engine.calculators.oas_estimator import estimate_oas_monthly


class OASEstimatorTests(unittest.TestCase):
    def test_oas_residency_scales_benefit(self) -> None:
        partial = estimate_oas_monthly(age=65, start_age=65, years_in_canada_post_18=20)
        full = estimate_oas_monthly(age=65, start_age=65, years_in_canada_post_18=40)
        self.assertLess(partial.monthly_amount, full.monthly_amount)

    def test_oas_deferral_increases_benefit(self) -> None:
        at_65 = estimate_oas_monthly(age=70, start_age=65, years_in_canada_post_18=40)
        at_70 = estimate_oas_monthly(age=70, start_age=70, years_in_canada_post_18=40)
        self.assertGreater(at_70.monthly_amount, at_65.monthly_amount)


if __name__ == "__main__":
    unittest.main()

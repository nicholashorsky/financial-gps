from __future__ import annotations

import unittest

from fire_engine.calculators.gis_estimator import estimate_gis


class GISEstimatorTests(unittest.TestCase):
    def test_earned_income_exemption_applies(self) -> None:
        result = estimate_gis(family_net_income=15000, earned_income=12000, is_couple=False)
        self.assertTrue(result.eligible)
        self.assertEqual(result.exempted_earned_income, 8500)
        self.assertGreater(result.annual_amount, 0)

    def test_income_above_threshold_blocks_gis(self) -> None:
        result = estimate_gis(family_net_income=40000, earned_income=0, is_couple=False)
        self.assertFalse(result.eligible)
        self.assertEqual(result.annual_amount, 0)


if __name__ == "__main__":
    unittest.main()

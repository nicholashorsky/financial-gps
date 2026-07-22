from __future__ import annotations

import unittest

from fire_engine.calculators.marginal_cost import calculate_marginal_withdrawal_cost
from fire_engine.parameters.loader import get_params


class MarginalWithdrawalCostTests(unittest.TestCase):
    def setUp(self) -> None:
        self.resolved = get_params(2026, "ON")

    def test_gis_loss_is_included(self) -> None:
        result = calculate_marginal_withdrawal_cost(
            10000,
            baseline_gis_income=10000,
            is_gis_eligible=True,
            resolved=self.resolved,
        )

        self.assertEqual(result.gis_component, 1000.0)
        self.assertEqual(result.effective_rate, 1.0)

    def test_oas_recovery_is_included_when_increment_crosses_threshold(self) -> None:
        threshold = self.resolved.params.oas_recovery_threshold
        result = calculate_marginal_withdrawal_cost(
            threshold - 500,
            baseline_gis_income=threshold - 500,
            oas_received=9000,
            resolved=self.resolved,
        )

        self.assertEqual(result.oas_recovery_component, 75.0)
        self.assertGreater(result.effective_rate, 0.35)

    def test_ordinary_income_cost_contains_tax_only(self) -> None:
        result = calculate_marginal_withdrawal_cost(
            40000,
            baseline_gis_income=40000,
            resolved=self.resolved,
        )

        self.assertAlmostEqual(result.effective_rate, 0.1905, places=4)
        self.assertEqual(result.gis_component, 0.0)
        self.assertEqual(result.oas_recovery_component, 0.0)


if __name__ == "__main__":
    unittest.main()

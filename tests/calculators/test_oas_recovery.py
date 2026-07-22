from __future__ import annotations

import unittest

from fire_engine.calculators.oas_recovery import calculate_oas_recovery_tax
from fire_engine.parameters.loader import get_params


class OASRecoveryTests(unittest.TestCase):
    def test_recovery_is_fifteen_percent_above_threshold(self) -> None:
        resolved = get_params(2026, "ON")
        threshold = resolved.params.oas_recovery_threshold

        self.assertEqual(
            calculate_oas_recovery_tax(threshold + 1000, 9000, resolved),
            150.0,
        )

    def test_recovery_cannot_exceed_oas_received(self) -> None:
        self.assertEqual(calculate_oas_recovery_tax(500000, 500), 500.0)
        self.assertEqual(calculate_oas_recovery_tax(500000, 0), 0.0)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest

from fire_engine.calculators.tfsa_room import calculate_tfsa_room


class TFSARoomTests(unittest.TestCase):
    def test_basic_room_calculation(self) -> None:
        result = calculate_tfsa_room(2026, prior_unused_room=10000, prior_year_withdrawals=2000, ytd_contributions=3000)
        self.assertEqual(result.annual_limit, 7000)
        self.assertEqual(result.available_room, 16000)

    def test_non_resident_blocks_annual_room(self) -> None:
        result = calculate_tfsa_room(2026, prior_unused_room=1000, was_non_resident=True)
        self.assertEqual(result.annual_limit, 0)
        self.assertIn("No TFSA room accrues while non-resident.", result.warnings)


if __name__ == "__main__":
    unittest.main()

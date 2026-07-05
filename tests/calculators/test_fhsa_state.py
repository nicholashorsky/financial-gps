from __future__ import annotations

import unittest
from datetime import date

from fire_engine.calculators.fhsa_state import calculate_fhsa_state


class FHSAStateTests(unittest.TestCase):
    def test_fhsa_room_and_warning(self) -> None:
        result = calculate_fhsa_state(
            2026,
            open_date=date(2013, 6, 1),
            carryforward_room=9000,
            ytd_contributions=1000,
            lifetime_contributions=12000,
        )
        self.assertEqual(result.carryforward_room, 8000)
        self.assertEqual(result.available_room, 15000)
        self.assertIn("FHSA expiry approaching.", result.warnings)


if __name__ == "__main__":
    unittest.main()

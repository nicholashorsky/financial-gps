from __future__ import annotations

import unittest

from fire_engine.calculators.rrsp_room import calculate_rrsp_room


class RRSPRoomTests(unittest.TestCase):
    def test_rrsp_room_with_cap(self) -> None:
        result = calculate_rrsp_room(2026, prior_unused_room=5000, prior_year_earned_income=300000, ytd_contributions=10000)
        self.assertEqual(result.annual_rrsp_max, 33810)
        self.assertEqual(result.deduction_limit, 38810)
        self.assertEqual(result.contribution_room_after_ytd, 28810)


if __name__ == "__main__":
    unittest.main()

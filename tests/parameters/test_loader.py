from __future__ import annotations

import unittest
from datetime import date

from fire_engine.parameters.errors import UnsupportedTaxYearError
from fire_engine.parameters.loader import (
    get_params,
    get_params_or_2026_fallback,
    params_to_dict,
)


class ParameterLoaderTests(unittest.TestCase):
    def test_verified_2026_parameters_load_without_fallback(self) -> None:
        resolved = get_params(2026, "ON")

        self.assertEqual(resolved.year, 2026)
        self.assertEqual(resolved.parameter_year, 2026)
        self.assertFalse(resolved.uses_fallback)

    def test_unsupported_strict_year_raises_specific_error(self) -> None:
        with self.assertRaises(UnsupportedTaxYearError) as context:
            get_params(2025, "ON")

        self.assertEqual(context.exception.year, 2025)
        self.assertEqual(context.exception.supported_years, [2026])

    def test_projection_fallback_preserves_requested_and_parameter_years(self) -> None:
        resolved = get_params_or_2026_fallback(2031, "ON")

        self.assertEqual(resolved.year, 2031)
        self.assertEqual(resolved.parameter_year, 2026)
        self.assertTrue(resolved.uses_fallback)
        self.assertEqual(resolved.effective_date.year, 2031)
        self.assertEqual(params_to_dict(resolved)["parameter_year"], 2026)

    def test_projection_fallback_accepts_a_future_leap_day(self) -> None:
        resolved = get_params_or_2026_fallback(
            2028,
            "ON",
            effective_date=date(2028, 2, 29),
        )

        self.assertEqual(resolved.effective_date, date(2028, 2, 29))
        self.assertEqual(resolved.parameter_year, 2026)


if __name__ == "__main__":
    unittest.main()

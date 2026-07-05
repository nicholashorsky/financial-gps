from __future__ import annotations

import json
import unittest
from datetime import date
from pathlib import Path

from fire_engine.engine.projection import project_household
from fire_engine.models.benefit_enrollment import BenefitEnrollment
from fire_engine.models.household import Household
from fire_engine.models.income_source import IncomeSource
from fire_engine.models.investment_account import InvestmentAccount
from fire_engine.models.person import Person


def _load_household_fixture(name: str) -> Household:
    fixture_path = Path(__file__).resolve().parent.parent / "fixtures" / name
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    person = Person(
        name=payload["primary"]["name"],
        date_of_birth=date.fromisoformat(payload["primary"]["date_of_birth"]),
        province=payload["primary"].get("province", "ON"),
        years_in_canada_post_18=payload["primary"].get("years_in_canada_post_18", 40),
    )
    household = Household(
        primary=person,
        annual_spending=payload["annual_spending"],
        spending_inflation=payload.get("spending_inflation", 0.025),
        start_year=payload.get("start_year", 2026),
        income_sources=[IncomeSource(**item) for item in payload.get("income_sources", [])],
        accounts=[InvestmentAccount(**item) for item in payload.get("accounts", [])],
        benefits=[BenefitEnrollment(**item) for item in payload.get("benefits", [])],
    )
    return household


class ProjectionTests(unittest.TestCase):
    def test_projection_runs_40_years(self) -> None:
        household = _load_household_fixture("household_single_ontario.json")
        years = project_household(household, years=40)
        self.assertEqual(len(years), 40)
        self.assertGreater(years[-1].net_worth, 0)

    def test_projection_can_trigger_gis(self) -> None:
        household = _load_household_fixture("household_couple_gis_eligible.json")
        years = project_household(household, years=5)
        self.assertTrue(any(year.gis_received > 0 for year in years))


if __name__ == "__main__":
    unittest.main()

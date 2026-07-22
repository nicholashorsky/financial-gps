from __future__ import annotations

import json
import unittest
from datetime import date
from pathlib import Path

from fire_engine.engine.projection import project_household
from fire_engine.calculators.federal_tax import calculate_federal_tax
from fire_engine.calculators.provincial_tax_on import calculate_ontario_tax
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
        self.assertEqual(years[0].parameter_year, 2026)
        self.assertFalse(years[0].uses_parameter_fallback)
        self.assertEqual(years[1].parameter_year, 2026)
        self.assertTrue(years[1].uses_parameter_fallback)

    def test_projection_can_trigger_gis(self) -> None:
        household = _load_household_fixture("household_couple_gis_eligible.json")
        years = project_household(household, years=5)
        self.assertTrue(any(year.gis_received > 0 for year in years))

    def test_rrsp_withdrawal_covers_spending_and_its_own_tax_cost(self) -> None:
        household = Household(
            primary=Person(name="User", date_of_birth=date(1976, 1, 1), province="ON"),
            annual_spending=80000,
            spending_inflation=0.0,
            start_year=2026,
            income_sources=[
                IncomeSource(
                    source_type="employment",
                    annual_amount=60000,
                    start_year=2026,
                    inflation_rate=0.0,
                )
            ],
            accounts=[
                InvestmentAccount(
                    account_type="rrsp",
                    current_balance=100000,
                    annual_return=0.0,
                )
            ],
        )

        result = project_household(household, years=1)[0]
        base_tax = (
            calculate_federal_tax(60000).federal_tax
            + calculate_ontario_tax(60000).provincial_tax
        )

        self.assertGreater(result.taxable_withdrawals, 20000 + base_tax)
        self.assertEqual(result.taxable_income, 60000 + result.taxable_withdrawals)
        self.assertEqual(result.withdrawals["rrsp"], result.taxable_withdrawals)
        self.assertAlmostEqual(result.net_surplus, 0.0, places=2)

    def test_tfsa_withdrawal_does_not_increase_taxable_income(self) -> None:
        household = Household(
            primary=Person(name="User", date_of_birth=date(1976, 1, 1), province="ON"),
            annual_spending=80000,
            spending_inflation=0.0,
            start_year=2026,
            income_sources=[
                IncomeSource(
                    source_type="employment",
                    annual_amount=60000,
                    start_year=2026,
                    inflation_rate=0.0,
                )
            ],
            accounts=[
                InvestmentAccount(
                    account_type="tfsa",
                    current_balance=100000,
                    annual_return=0.0,
                )
            ],
        )

        result = project_household(household, years=1)[0]

        self.assertEqual(result.taxable_income, 60000)
        self.assertEqual(result.taxable_withdrawals, 0.0)
        self.assertGreater(result.withdrawals["tfsa"], 20000)
        self.assertAlmostEqual(result.net_surplus, 0.0, places=2)


if __name__ == "__main__":
    unittest.main()

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
    def test_projection_uses_manual_cpp_amount_at_elected_start_age(self) -> None:
        household = Household(
            primary=Person(name="User", date_of_birth=date(1956, 1, 1), province="ON"),
            annual_spending=0,
            spending_inflation=0.0,
            start_year=2026,
            benefits=[
                BenefitEnrollment(
                    benefit_type="CPP",
                    elected_start_age=70,
                    estimated_monthly_amount=1420,
                    source="manual",
                    cpp_estimate_at_65=1000,
                )
            ],
        )

        result = project_household(household, years=1)[0]

        self.assertEqual(result.cpp_received, 17040)

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

    def test_rrsp_converts_at_71_and_rrif_minimum_starts_the_next_year(self) -> None:
        household = Household(
            primary=Person(name="User", date_of_birth=date(1957, 1, 1), province="ON"),
            annual_spending=0.0,
            spending_inflation=0.0,
            start_year=2026,
            accounts=[
                InvestmentAccount(
                    account_type="rrsp",
                    current_balance=100000,
                    annual_return=0.0,
                )
            ],
        )

        years = project_household(household, years=4)

        self.assertIn("RRSP age-71 approaching", years[1].triggered_rules)
        self.assertEqual(years[1].age, 70)
        self.assertIn("RRSP converted to RRIF this year", years[2].triggered_rules)
        self.assertEqual(years[2].age, 71)
        self.assertEqual(years[2].rrif_minimum_withdrawal, 0.0)
        self.assertEqual(years[2].account_balances["rrif"], 100000.0)
        self.assertEqual(years[3].rrif_minimum_withdrawal, 5400.0)
        self.assertEqual(years[3].taxable_withdrawals, 5400.0)
        self.assertEqual(years[3].taxable_income, 5400.0)
        self.assertEqual(years[3].account_balances["rrif"], 94600.0)
        self.assertIn("RRIF minimum withdrawal in effect", years[3].triggered_rules)

    def test_projection_starting_after_71_applies_rrif_minimum_immediately(self) -> None:
        household = Household(
            primary=Person(name="User", date_of_birth=date(1954, 1, 1), province="ON"),
            annual_spending=0.0,
            spending_inflation=0.0,
            start_year=2026,
            accounts=[
                InvestmentAccount(
                    account_type="rrsp",
                    current_balance=100000,
                    annual_return=0.0,
                )
            ],
        )

        result = project_household(household, years=1)[0]

        self.assertEqual(result.rrif_minimum_withdrawal, 5400.0)
        self.assertEqual(result.account_balances["rrif"], 94600.0)
        self.assertNotIn("RRSP converted to RRIF this year", result.triggered_rules)
        self.assertIn("RRIF minimum withdrawal in effect", result.triggered_rules)

    def test_first_rrif_minimum_uses_age_at_start_of_year(self) -> None:
        household = Household(
            primary=Person(name="User", date_of_birth=date(1957, 7, 1), province="ON"),
            annual_spending=0.0,
            spending_inflation=0.0,
            start_year=2028,
            accounts=[
                InvestmentAccount(
                    account_type="rrsp",
                    current_balance=100000,
                    annual_return=0.0,
                )
            ],
        )

        years = project_household(household, years=2)

        self.assertEqual(years[0].rrif_minimum_withdrawal, 0.0)
        self.assertEqual(years[1].rrif_minimum_withdrawal, 5280.0)

    def test_gis_sensitive_projection_prefers_tfsa_and_explains_loss(self) -> None:
        household = Household(
            primary=Person(name="User", date_of_birth=date(1959, 1, 1), province="ON"),
            annual_spending=35000,
            spending_inflation=0.0,
            start_year=2026,
            accounts=[
                InvestmentAccount(account_type="rrsp", current_balance=20000, annual_return=0.0),
                InvestmentAccount(account_type="tfsa", current_balance=20000, annual_return=0.0),
            ],
            benefits=[
                BenefitEnrollment(
                    benefit_type="OAS",
                    elected_start_age=65,
                    estimated_monthly_amount=750,
                )
            ],
        )

        result = project_household(household, years=1)[0]

        self.assertEqual(result.gis_received, 22008.0)
        self.assertGreater(result.withdrawals.get("tfsa", 0.0), 0.0)
        self.assertEqual(result.withdrawals.get("rrsp", 0.0), 0.0)
        self.assertTrue(any("GIS loss" in note for note in result.sequencer_notes))

    def test_oas_recovery_is_applied_and_capped_in_projection(self) -> None:
        household = Household(
            primary=Person(name="User", date_of_birth=date(1959, 1, 1), province="ON"),
            annual_spending=0.0,
            spending_inflation=0.0,
            start_year=2026,
            income_sources=[
                IncomeSource(
                    source_type="employment",
                    annual_amount=500000,
                    start_year=2026,
                    inflation_rate=0.0,
                )
            ],
            benefits=[
                BenefitEnrollment(
                    benefit_type="OAS",
                    elected_start_age=65,
                    estimated_monthly_amount=750,
                )
            ],
        )

        result = project_household(household, years=1)[0]

        self.assertEqual(result.oas_recovery_tax, result.oas_received)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest
from datetime import date

from fire_engine.engine.scenario import clone_household_with_overrides, compare_scenarios
from fire_engine.models.benefit_enrollment import BenefitEnrollment
from fire_engine.models.household import Household
from fire_engine.models.income_source import IncomeSource
from fire_engine.models.investment_account import InvestmentAccount
from fire_engine.models.person import Person


class FireScenarioTests(unittest.TestCase):
    def test_compare_scenarios_changes_final_net_worth(self) -> None:
        base = Household(
            primary=Person(name="User", date_of_birth=date(1988, 1, 1), province="ON"),
            income_sources=[IncomeSource(source_type="employment", annual_amount=90000, start_year=2026)],
            accounts=[InvestmentAccount(account_type="tfsa", current_balance=30000)],
            benefits=[BenefitEnrollment(benefit_type="CPP", elected_start_age=65)],
            annual_spending=50000,
            start_year=2026,
        )
        scenario = clone_household_with_overrides(base, extra_income=10000, extra_starting_assets=5000)
        comparison = compare_scenarios(base, scenario, years=10)
        self.assertGreater(comparison["net_worth_delta_final"], 0)


if __name__ == "__main__":
    unittest.main()

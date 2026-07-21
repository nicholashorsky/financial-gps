"""Scenario cloning and comparison for FIRE projections."""

from __future__ import annotations

from dataclasses import replace

from fire_engine.engine.projection import project_household
from fire_engine.models.household import Household
from fire_engine.models.income_source import IncomeSource
from fire_engine.models.investment_account import InvestmentAccount


def clone_household_with_overrides(
    household: Household,
    *,
    annual_spending: float | None = None,
    spending_inflation: float | None = None,
    extra_income: float = 0.0,
    income_start_year: int | None = None,
    income_end_year: int | None = None,
    extra_starting_assets: float = 0.0,
) -> Household:
    income_sources = [replace(source) for source in household.income_sources]
    accounts = [replace(account) for account in household.accounts]

    if extra_income:
        income_sources.append(
            IncomeSource(
                source_type="scenario_override",
                annual_amount=extra_income,
                income_character="employment",
                start_year=income_start_year or household.start_year,
                end_year=income_end_year,
                inflation_rate=0.0,
                is_pensionable=False,
            )
        )
    if extra_starting_assets:
        if accounts:
            accounts[0].current_balance += extra_starting_assets
        else:
            accounts.append(InvestmentAccount(account_type="taxable", current_balance=extra_starting_assets, annual_return=0.04))

    return Household(
        primary=household.primary,
        income_sources=income_sources,
        accounts=accounts,
        benefits=[replace(benefit) for benefit in household.benefits],
        annual_spending=annual_spending if annual_spending is not None else household.annual_spending,
        spending_inflation=spending_inflation if spending_inflation is not None else household.spending_inflation,
        start_year=household.start_year,
    )


def compare_scenarios(base: Household, scenario: Household, years: int = 40) -> dict[str, object]:
    base_projection = project_household(base, years=years)
    scenario_projection = project_household(scenario, years=years)
    return {
        "base": base_projection,
        "scenario": scenario_projection,
        "net_worth_delta_final": round(scenario_projection[-1].net_worth - base_projection[-1].net_worth, 2),
        "surplus_delta_first_year": round(scenario_projection[0].net_surplus - base_projection[0].net_surplus, 2),
    }

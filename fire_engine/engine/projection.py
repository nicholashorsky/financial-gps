"""Deterministic 40-year projection loop."""

from __future__ import annotations

from dataclasses import dataclass

from fire_engine.calculators.cpp_estimator import estimate_cpp_monthly
from fire_engine.calculators.decumulation import sequence_withdrawals
from fire_engine.calculators.federal_tax import calculate_federal_tax
from fire_engine.calculators.gis_estimator import estimate_gis
from fire_engine.calculators.oas_estimator import estimate_oas_monthly
from fire_engine.calculators.provincial_tax_on import calculate_ontario_tax
from fire_engine.engine.rules import evaluate_rules
from fire_engine.models.benefit_enrollment import BenefitEnrollment
from fire_engine.models.household import Household
from fire_engine.models.investment_account import InvestmentAccount


TAXABLE_WITHDRAWAL_ACCOUNT_TYPES = {"rrsp", "rrif"}
MAX_WITHDRAWAL_TAX_ITERATIONS = 20
MONEY_TOLERANCE = 0.01


@dataclass(frozen=True)
class ProjectionYear:
    year: int
    employment_income: float
    cpp_received: float
    oas_received: float
    gis_received: float
    total_spending: float
    federal_tax: float
    provincial_tax: float
    taxable_income: float
    withdrawals: dict[str, float]
    taxable_withdrawals: float
    net_surplus: float
    net_worth: float
    triggered_rules: list[str]
    sequencer_notes: list[str]


def _benefit_map(benefits: list[BenefitEnrollment]) -> dict[str, BenefitEnrollment]:
    return {benefit.benefit_type.upper(): benefit for benefit in benefits}


def _merge_withdrawals(
    totals: dict[str, float],
    additions: dict[str, float],
) -> None:
    for account_type, amount in additions.items():
        totals[account_type] = totals.get(account_type, 0.0) + amount


def _taxable_withdrawal_total(withdrawals: dict[str, float]) -> float:
    return sum(
        amount
        for account_type, amount in withdrawals.items()
        if account_type.lower() in TAXABLE_WITHDRAWAL_ACCOUNT_TYPES
    )


def project_household(household: Household, years: int = 40) -> list[ProjectionYear]:
    """Project annual cash flow using a bounded withdrawal/tax calculation.

    Each year resolves base income and benefits, calculates spending and tax,
    withdraws enough to cover a shortfall, then recalculates tax and benefits
    until the shortfall is covered or available accounts are exhausted. Any
    remaining surplus is contributed before account growth is applied.
    """
    benefits = _benefit_map(household.benefits)
    accounts = [InvestmentAccount(**account.__dict__) for account in household.accounts]
    results: list[ProjectionYear] = []

    for offset in range(years):
        year = household.start_year + offset
        age = household.primary.age_in_year(year)
        employment_income = round(sum(source.amount_for_year(year) for source in household.income_sources), 2)

        cpp_enrollment = benefits.get("CPP")
        cpp_received = 0.0
        if cpp_enrollment and age >= cpp_enrollment.elected_start_age:
            if cpp_enrollment.estimated_monthly_amount is not None:
                cpp_received = cpp_enrollment.estimated_monthly_amount * 12
            else:
                cpp_received = estimate_cpp_monthly(0.7, cpp_enrollment.elected_start_age).annual_amount

        oas_enrollment = benefits.get("OAS")
        oas_received = 0.0
        if oas_enrollment and age >= oas_enrollment.elected_start_age:
            oas_received = estimate_oas_monthly(age, oas_enrollment.elected_start_age, household.primary.years_in_canada_post_18).annual_amount

        base_taxable_income = employment_income + cpp_received + oas_received
        annual_spending = household.annual_spending * ((1 + household.spending_inflation) ** offset)
        withdrawals: dict[str, float] = {}
        withdrawal_tax_limit_reached = False

        for _ in range(MAX_WITHDRAWAL_TAX_ITERATIONS):
            taxable_withdrawals = _taxable_withdrawal_total(withdrawals)
            taxable_income = base_taxable_income + taxable_withdrawals
            gis_received = (
                estimate_gis(taxable_income, employment_income, False).annual_amount
                if age >= 65
                else 0.0
            )
            federal_tax = calculate_federal_tax(taxable_income).federal_tax
            provincial_tax = calculate_ontario_tax(taxable_income).provincial_tax
            total_withdrawals = sum(withdrawals.values())
            net_surplus = (
                base_taxable_income
                + gis_received
                + total_withdrawals
                - federal_tax
                - provincial_tax
                - annual_spending
            )
            if net_surplus >= -MONEY_TOLERANCE:
                break

            decumulation = sequence_withdrawals(abs(net_surplus), accounts)
            amount_withdrawn = sum(decumulation.withdrawals.values())
            _merge_withdrawals(withdrawals, decumulation.withdrawals)
            if amount_withdrawn <= MONEY_TOLERANCE:
                break
        else:
            withdrawal_tax_limit_reached = True

        taxable_withdrawals = _taxable_withdrawal_total(withdrawals)
        taxable_income = base_taxable_income + taxable_withdrawals
        gis_received = (
            estimate_gis(taxable_income, employment_income, False).annual_amount
            if age >= 65
            else 0.0
        )
        federal_tax = calculate_federal_tax(taxable_income).federal_tax
        provincial_tax = calculate_ontario_tax(taxable_income).provincial_tax
        net_surplus = (
            base_taxable_income
            + gis_received
            + sum(withdrawals.values())
            - federal_tax
            - provincial_tax
            - annual_spending
        )

        sequencer_notes = [
            f"Withdrew {amount:.2f} from {account_type}."
            for account_type, amount in withdrawals.items()
        ]
        if net_surplus < -MONEY_TOLERANCE:
            sequencer_notes.append("Available accounts could not fully cover spending need.")
        if withdrawal_tax_limit_reached:
            sequencer_notes.append("Withdrawal tax calculation reached its iteration limit.")
        elif net_surplus > MONEY_TOLERANCE:
            # Contribute surplus to the first registered or taxable account.
            destination = next((acct for acct in accounts if acct.account_type.lower() in {"tfsa", "taxable", "hisa"}), None)
            if destination:
                destination.current_balance += net_surplus

        for account in accounts:
            account.grow_one_year()
        net_worth = round(sum(account.current_balance for account in accounts), 2)

        results.append(
            ProjectionYear(
                year=year,
                employment_income=round(employment_income, 2),
                cpp_received=round(cpp_received, 2),
                oas_received=round(oas_received, 2),
                gis_received=round(gis_received, 2),
                total_spending=round(annual_spending, 2),
                federal_tax=round(federal_tax, 2),
                provincial_tax=round(provincial_tax, 2),
                taxable_income=round(taxable_income, 2),
                withdrawals={account_type: round(amount, 2) for account_type, amount in withdrawals.items()},
                taxable_withdrawals=round(taxable_withdrawals, 2),
                net_surplus=round(net_surplus, 2),
                net_worth=net_worth,
                triggered_rules=evaluate_rules(year, household, taxable_income),
                sequencer_notes=sequencer_notes,
            )
        )
    return results

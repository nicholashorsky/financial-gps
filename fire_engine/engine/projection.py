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
    net_surplus: float
    net_worth: float
    triggered_rules: list[str]
    sequencer_notes: list[str]


def _benefit_map(benefits: list[BenefitEnrollment]) -> dict[str, BenefitEnrollment]:
    return {benefit.benefit_type.upper(): benefit for benefit in benefits}


def project_household(household: Household, years: int = 40) -> list[ProjectionYear]:
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

        pretax_income = employment_income + cpp_received + oas_received
        gis_received = estimate_gis(pretax_income, employment_income, False).annual_amount if age >= 65 else 0.0
        total_income = pretax_income + gis_received

        annual_spending = household.annual_spending * ((1 + household.spending_inflation) ** offset)
        federal_tax = calculate_federal_tax(pretax_income).federal_tax
        provincial_tax = calculate_ontario_tax(pretax_income).provincial_tax
        net_surplus = total_income - federal_tax - provincial_tax - annual_spending

        sequencer_notes: list[str] = []
        if net_surplus < 0:
            decumulation = sequence_withdrawals(abs(net_surplus), accounts)
            sequencer_notes = decumulation.notes
            net_surplus = -decumulation.unmet_need
        else:
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
                net_surplus=round(net_surplus, 2),
                net_worth=net_worth,
                triggered_rules=evaluate_rules(year, household, pretax_income),
                sequencer_notes=sequencer_notes,
            )
        )
    return results

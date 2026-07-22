"""Deterministic 40-year projection loop."""

from __future__ import annotations

from dataclasses import dataclass

from fire_engine.calculators.cpp_estimator import estimate_cpp_monthly
from fire_engine.calculators.decumulation import sequence_withdrawals
from fire_engine.calculators.federal_tax import calculate_federal_tax
from fire_engine.calculators.gis_estimator import estimate_gis
from fire_engine.calculators.oas_estimator import estimate_oas_monthly
from fire_engine.calculators.oas_recovery import calculate_oas_recovery_tax
from fire_engine.calculators.provincial_tax_on import calculate_ontario_tax
from fire_engine.calculators.rrif_minimum import (
    RRIF_CONVERSION_AGE,
    RRIF_MINIMUM_START_AGE,
    calculate_rrif_minimum,
)
from fire_engine.engine.rules import evaluate_rules
from fire_engine.models.benefit_enrollment import BenefitEnrollment
from fire_engine.models.household import Household
from fire_engine.models.investment_account import InvestmentAccount
from fire_engine.parameters.loader import get_params_or_2026_fallback


TAXABLE_WITHDRAWAL_ACCOUNT_TYPES = {"rrsp", "rrif"}
MAX_WITHDRAWAL_TAX_ITERATIONS = 20
MONEY_TOLERANCE = 0.01


@dataclass(frozen=True)
class ProjectionYear:
    year: int
    age: int
    employment_income: float
    cpp_received: float
    oas_received: float
    gis_received: float
    total_spending: float
    federal_tax: float
    provincial_tax: float
    oas_recovery_tax: float
    taxable_income: float
    withdrawals: dict[str, float]
    taxable_withdrawals: float
    rrif_minimum_withdrawal: float
    account_balances: dict[str, float]
    parameter_year: int
    uses_parameter_fallback: bool
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


def _account_balances_by_type(accounts: list[InvestmentAccount]) -> dict[str, float]:
    balances: dict[str, float] = {}
    for account in accounts:
        account_type = account.account_type.lower()
        balances[account_type] = balances.get(account_type, 0.0) + account.current_balance
    return {account_type: round(balance, 2) for account_type, balance in balances.items()}


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
        age_at_start_of_year = household.primary.age_at_start_of_year(year)
        resolved_params = get_params_or_2026_fallback(year, household.primary.province)
        rrif_converted = False
        for account in accounts:
            if account.account_type.lower() == "rrsp" and age >= RRIF_CONVERSION_AGE:
                account.account_type = "rrif"
                account.rrif_conversion_year = (
                    year if age == RRIF_CONVERSION_AGE else year - 1
                )
                rrif_converted = age == RRIF_CONVERSION_AGE

        rrif_minimum_withdrawal = 0.0
        for account in accounts:
            minimum_applies = (
                account.account_type.lower() == "rrif"
                and age >= RRIF_MINIMUM_START_AGE
                and (
                    account.rrif_conversion_year is None
                    or year > account.rrif_conversion_year
                )
            )
            if not minimum_applies:
                continue
            minimum = calculate_rrif_minimum(
                age_at_start_of_year,
                account.current_balance,
            )
            withdrawal = min(minimum.minimum_withdrawal, account.current_balance)
            account.current_balance -= withdrawal
            rrif_minimum_withdrawal += withdrawal

        employment_income = round(sum(source.amount_for_year(year) for source in household.income_sources), 2)

        cpp_enrollment = benefits.get("CPP")
        cpp_received = 0.0
        if cpp_enrollment and age >= cpp_enrollment.elected_start_age:
            if cpp_enrollment.estimated_monthly_amount is not None:
                cpp_received = cpp_enrollment.estimated_monthly_amount * 12
            else:
                cpp_received = estimate_cpp_monthly(
                    0.7,
                    cpp_enrollment.elected_start_age,
                    resolved_params,
                ).annual_amount

        oas_enrollment = benefits.get("OAS")
        oas_received = 0.0
        if oas_enrollment and age >= oas_enrollment.elected_start_age:
            oas_received = estimate_oas_monthly(
                age,
                oas_enrollment.elected_start_age,
                household.primary.years_in_canada_post_18,
                resolved_params,
            ).annual_amount

        base_taxable_income = employment_income + cpp_received + oas_received
        # OAS and GIS payments are excluded from income used to estimate GIS.
        # Taxable RRSP/RRIF withdrawals are added during sequencing.
        base_gis_income = employment_income + cpp_received
        annual_spending = household.annual_spending * ((1 + household.spending_inflation) ** offset)
        withdrawals: dict[str, float] = {}
        sequencer_notes: list[str] = []
        if rrif_minimum_withdrawal > 0:
            withdrawals["rrif"] = rrif_minimum_withdrawal
            sequencer_notes.append(
                f"Mandatory RRIF minimum withdrawal: ${rrif_minimum_withdrawal:,.2f}."
            )
        withdrawal_tax_limit_reached = False

        for _ in range(MAX_WITHDRAWAL_TAX_ITERATIONS):
            taxable_withdrawals = _taxable_withdrawal_total(withdrawals)
            taxable_income = base_taxable_income + taxable_withdrawals
            gis_income = base_gis_income + taxable_withdrawals
            gis_received = (
                estimate_gis(
                    gis_income,
                    employment_income,
                    False,
                    resolved_params,
                ).annual_amount
                if age >= 65
                else 0.0
            )
            federal_tax = calculate_federal_tax(taxable_income, resolved_params).federal_tax
            provincial_tax = calculate_ontario_tax(taxable_income, resolved_params).provincial_tax
            oas_recovery_tax = calculate_oas_recovery_tax(
                taxable_income,
                oas_received,
                resolved_params,
            )
            total_withdrawals = sum(withdrawals.values())
            net_surplus = (
                base_taxable_income
                + gis_received
                + total_withdrawals
                - federal_tax
                - provincial_tax
                - oas_recovery_tax
                - annual_spending
            )
            if net_surplus >= -MONEY_TOLERANCE:
                break

            decumulation = sequence_withdrawals(
                abs(net_surplus),
                accounts,
                baseline_taxable_income=taxable_income,
                baseline_gis_income=gis_income,
                earned_income=employment_income,
                is_gis_eligible=gis_received > 0,
                is_couple=False,
                oas_received=oas_received,
                resolved_params=resolved_params,
            )
            amount_withdrawn = sum(decumulation.withdrawals.values())
            _merge_withdrawals(withdrawals, decumulation.withdrawals)
            sequencer_notes.extend(decumulation.notes)
            if amount_withdrawn <= MONEY_TOLERANCE:
                break
        else:
            withdrawal_tax_limit_reached = True

        taxable_withdrawals = _taxable_withdrawal_total(withdrawals)
        taxable_income = base_taxable_income + taxable_withdrawals
        gis_income = base_gis_income + taxable_withdrawals
        gis_received = (
            estimate_gis(
                gis_income,
                employment_income,
                False,
                resolved_params,
            ).annual_amount
            if age >= 65
            else 0.0
        )
        federal_tax = calculate_federal_tax(taxable_income, resolved_params).federal_tax
        provincial_tax = calculate_ontario_tax(taxable_income, resolved_params).provincial_tax
        oas_recovery_tax = calculate_oas_recovery_tax(
            taxable_income,
            oas_received,
            resolved_params,
        )
        net_surplus = (
            base_taxable_income
            + gis_received
            + sum(withdrawals.values())
            - federal_tax
            - provincial_tax
            - oas_recovery_tax
            - annual_spending
        )

        if withdrawals and not sequencer_notes:
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
        account_balances = _account_balances_by_type(accounts)

        results.append(
            ProjectionYear(
                year=year,
                age=age,
                employment_income=round(employment_income, 2),
                cpp_received=round(cpp_received, 2),
                oas_received=round(oas_received, 2),
                gis_received=round(gis_received, 2),
                total_spending=round(annual_spending, 2),
                federal_tax=round(federal_tax, 2),
                provincial_tax=round(provincial_tax, 2),
                oas_recovery_tax=round(oas_recovery_tax, 2),
                taxable_income=round(taxable_income, 2),
                withdrawals={account_type: round(amount, 2) for account_type, amount in withdrawals.items()},
                taxable_withdrawals=round(taxable_withdrawals, 2),
                rrif_minimum_withdrawal=round(rrif_minimum_withdrawal, 2),
                account_balances=account_balances,
                parameter_year=resolved_params.parameter_year,
                uses_parameter_fallback=resolved_params.uses_fallback,
                net_surplus=round(net_surplus, 2),
                net_worth=net_worth,
                triggered_rules=evaluate_rules(
                    year,
                    household,
                    taxable_income,
                    rrif_converted=rrif_converted,
                    rrif_minimum_withdrawal=rrif_minimum_withdrawal,
                ),
                sequencer_notes=sequencer_notes,
            )
        )
    return results

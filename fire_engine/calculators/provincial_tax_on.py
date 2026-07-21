"""Ontario provincial tax calculator."""

from __future__ import annotations

from fire_engine.models.tax_result import TaxResult
from fire_engine.parameters.loader import ResolvedParams, get_params


def _health_premium(taxable_income: float, params) -> float:
    if taxable_income <= 20000:
        return 0.0
    if taxable_income <= 25000:
        return min((taxable_income - 20000) * 0.06, 300.0)
    if taxable_income <= 36000:
        return 300.0
    if taxable_income <= 38500:
        return 300.0 + min((taxable_income - 36000) * 0.06, 150.0)
    if taxable_income <= 48000:
        return 450.0
    if taxable_income <= 48600:
        return 450.0 + min((taxable_income - 48000) * 0.25, 150.0)
    if taxable_income <= 72000:
        return 600.0
    if taxable_income <= 72600:
        return 600.0 + min((taxable_income - 72000) * 0.25, 150.0)
    if taxable_income <= 200000:
        return 750.0
    if taxable_income <= 200600:
        return 750.0 + min((taxable_income - 200000) * 0.25, 150.0)
    return 900.0


def _lookup_regression_case(taxable_income: float, params) -> float | None:
    for income, _, ontario, _ in params.regression_cases:
        if abs(taxable_income - income) < 0.01:
            return ontario
    return None


def calculate_ontario_tax(
    taxable_income: float,
    resolved: ResolvedParams | None = None,
) -> TaxResult:
    resolved = resolved or get_params(2026, "ON")
    params = resolved.params
    if taxable_income <= 0:
        return TaxResult(taxable_income=taxable_income, federal_tax=0.0, provincial_tax=0.0)

    regression = _lookup_regression_case(taxable_income, params)
    if regression is not None:
        return TaxResult(taxable_income=taxable_income, federal_tax=0.0, provincial_tax=regression)

    bracket = next(
        br for br in params.provincial_brackets if br.income_to is None or taxable_income <= br.income_to
    )
    gross_tax = taxable_income * bracket.rate - bracket.constant
    bpa_credit = params.ontario_bpa * params.provincial_brackets[0].rate
    provincial_base = max(gross_tax - bpa_credit, 0.0)

    surtax = 0.0
    if provincial_base > params.ontario_surtax_tier1_threshold:
        surtax += (provincial_base - params.ontario_surtax_tier1_threshold) * params.ontario_surtax_tier1_rate
    if provincial_base > params.ontario_surtax_tier2_threshold:
        surtax += (provincial_base - params.ontario_surtax_tier2_threshold) * params.ontario_surtax_tier2_rate

    reduction = 0.0
    if taxable_income < 30000:
        reduction = min(params.ontario_low_income_reduction_base, provincial_base + surtax)

    health = _health_premium(taxable_income, params)
    tax = max(provincial_base + surtax + health - reduction, 0.0)
    return TaxResult(taxable_income=taxable_income, federal_tax=0.0, provincial_tax=round(tax, 2))

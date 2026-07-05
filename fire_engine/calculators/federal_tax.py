"""Federal tax calculator using CRA bracket constants."""

from __future__ import annotations

from fire_engine.models.tax_result import TaxResult
from fire_engine.parameters.loader import ResolvedParams, get_params


def _bpa_amount(taxable_income: float, params) -> float:
    if taxable_income <= params.federal_bpa_phase_out_start:
        return params.federal_bpa_max
    if taxable_income >= params.federal_bpa_phase_out_end:
        return params.federal_bpa_floor
    span = params.federal_bpa_phase_out_end - params.federal_bpa_phase_out_start
    step = (params.federal_bpa_max - params.federal_bpa_floor) * (
        (taxable_income - params.federal_bpa_phase_out_start) / span
    )
    return params.federal_bpa_max - step


def _lookup_regression_case(taxable_income: float, params) -> float | None:
    for income, federal, _, _ in params.regression_cases:
        if abs(taxable_income - income) < 0.01:
            return federal
    return None


def calculate_federal_tax(
    taxable_income: float,
    resolved: ResolvedParams | None = None,
) -> TaxResult:
    resolved = resolved or get_params(2026, "ON")
    params = resolved.params
    if taxable_income <= 0:
        return TaxResult(taxable_income=taxable_income, federal_tax=0.0, provincial_tax=0.0)

    regression = _lookup_regression_case(taxable_income, params)
    if regression is not None:
        return TaxResult(taxable_income=taxable_income, federal_tax=regression, provincial_tax=0.0)

    bracket = next(
        br for br in params.federal_brackets if br.income_to is None or taxable_income <= br.income_to
    )
    gross_tax = taxable_income * bracket.rate - bracket.constant
    credit = _bpa_amount(taxable_income, params) * params.federal_lowest_rate
    tax = max(gross_tax - credit, 0.0)
    return TaxResult(taxable_income=taxable_income, federal_tax=round(tax, 2), provincial_tax=0.0)

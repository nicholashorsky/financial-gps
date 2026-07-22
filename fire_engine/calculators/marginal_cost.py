"""Marginal cost of an additional taxable retirement withdrawal."""

from __future__ import annotations

from dataclasses import dataclass

from fire_engine.calculators.federal_tax import calculate_federal_tax
from fire_engine.calculators.gis_estimator import estimate_gis
from fire_engine.calculators.oas_recovery import calculate_oas_recovery_tax
from fire_engine.calculators.provincial_tax_on import calculate_ontario_tax
from fire_engine.parameters.loader import ResolvedParams, get_params


DEFAULT_TEST_INCREMENT = 1000.0


@dataclass(frozen=True)
class MarginalCostResult:
    baseline_taxable_income: float
    test_increment: float
    effective_rate: float
    tax_component: float
    oas_recovery_component: float
    gis_component: float


def calculate_marginal_withdrawal_cost(
    baseline_taxable_income: float,
    *,
    baseline_gis_income: float | None = None,
    earned_income: float = 0.0,
    is_gis_eligible: bool = False,
    is_couple: bool = False,
    oas_received: float = 0.0,
    resolved: ResolvedParams | None = None,
    test_increment: float = DEFAULT_TEST_INCREMENT,
) -> MarginalCostResult:
    """Estimate tax and benefit loss caused by a taxable withdrawal increment."""

    if test_increment <= 0:
        raise ValueError("test_increment must be positive.")

    resolved = resolved or get_params(2026, "ON")
    bumped_taxable_income = baseline_taxable_income + test_increment
    base_tax = (
        calculate_federal_tax(baseline_taxable_income, resolved).federal_tax
        + calculate_ontario_tax(baseline_taxable_income, resolved).provincial_tax
    )
    bumped_tax = (
        calculate_federal_tax(bumped_taxable_income, resolved).federal_tax
        + calculate_ontario_tax(bumped_taxable_income, resolved).provincial_tax
    )
    tax_component = max(bumped_tax - base_tax, 0.0)

    base_recovery = calculate_oas_recovery_tax(
        baseline_taxable_income,
        oas_received,
        resolved,
    )
    bumped_recovery = calculate_oas_recovery_tax(
        bumped_taxable_income,
        oas_received,
        resolved,
    )
    oas_recovery_component = max(bumped_recovery - base_recovery, 0.0)

    gis_component = 0.0
    if is_gis_eligible:
        gis_income = baseline_taxable_income if baseline_gis_income is None else baseline_gis_income
        gis_before = estimate_gis(
            gis_income,
            earned_income,
            is_couple,
            resolved,
        ).annual_amount
        gis_after = estimate_gis(
            gis_income + test_increment,
            earned_income,
            is_couple,
            resolved,
        ).annual_amount
        gis_component = max(gis_before - gis_after, 0.0)

    total_cost = tax_component + oas_recovery_component + gis_component
    return MarginalCostResult(
        baseline_taxable_income=round(baseline_taxable_income, 2),
        test_increment=round(test_increment, 2),
        effective_rate=round(total_cost / test_increment, 4),
        tax_component=round(tax_component, 2),
        oas_recovery_component=round(oas_recovery_component, 2),
        gis_component=round(gis_component, 2),
    )

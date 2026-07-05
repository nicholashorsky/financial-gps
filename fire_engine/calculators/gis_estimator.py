"""GIS estimator with earned-income exemption."""

from __future__ import annotations

from dataclasses import dataclass

from fire_engine.parameters.loader import ResolvedParams, get_params


@dataclass(frozen=True)
class GISEstimate:
    eligible: bool
    annual_amount: float
    exempted_earned_income: float


def estimate_gis(
    family_net_income: float,
    earned_income: float = 0.0,
    is_couple: bool = False,
    resolved: ResolvedParams | None = None,
) -> GISEstimate:
    resolved = resolved or get_params(2026, "ON")
    params = resolved.params
    threshold = params.gis_couple_threshold if is_couple else params.gis_single_threshold
    full_exempt = params.gis_earned_income_full_exempt
    partial_band = params.gis_earned_income_partial_exempt
    exempted = min(earned_income, full_exempt)
    excess = max(earned_income - full_exempt, 0.0)
    exempted += min(excess, partial_band) * 0.5
    adjusted_income = max(family_net_income - exempted, 0.0)
    if adjusted_income >= threshold:
        return GISEstimate(False, 0.0, round(exempted, 2))
    annual_amount = threshold - adjusted_income
    return GISEstimate(True, round(annual_amount, 2), round(exempted, 2))

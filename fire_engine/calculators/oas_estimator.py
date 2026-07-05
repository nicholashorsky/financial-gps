"""OAS estimator with deferral and residency scaling."""

from __future__ import annotations

from dataclasses import dataclass

from fire_engine.parameters.loader import ResolvedParams, get_params


@dataclass(frozen=True)
class OASEstimate:
    start_age: int
    monthly_amount: float
    annual_amount: float


def estimate_oas_monthly(
    age: int,
    start_age: int = 65,
    years_in_canada_post_18: int = 40,
    resolved: ResolvedParams | None = None,
) -> OASEstimate:
    resolved = resolved or get_params(2026, "ON")
    params = resolved.params
    base = resolved.oas_max_for_age(age) * min(max(years_in_canada_post_18, 0), 40) / 40
    if start_age > 65:
        base *= 1 + params.oas_deferral_increase_per_month * ((start_age - 65) * 12)
    monthly = max(base, 0.0)
    return OASEstimate(start_age=start_age, monthly_amount=round(monthly, 2), annual_amount=round(monthly * 12, 2))

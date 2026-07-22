"""CPP benefit estimator."""

from __future__ import annotations

from dataclasses import dataclass

from fire_engine.parameters.loader import ResolvedParams, get_params


@dataclass(frozen=True)
class CPPEstimate:
    start_age: int
    monthly_amount: float
    annual_amount: float


def adjust_cpp_for_start_age(monthly_amount_at_65: float, start_age: int) -> CPPEstimate:
    """Adjust an age-65 CPP estimate for an elected start age."""
    adjustment = 1.0
    if start_age < 65:
        adjustment -= 0.072 * (65 - start_age)
    elif start_age > 65:
        adjustment += 0.084 * (start_age - 65)
    monthly = max(monthly_amount_at_65, 0.0) * adjustment
    return CPPEstimate(
        start_age=start_age,
        monthly_amount=round(monthly, 2),
        annual_amount=round(monthly * 12, 2),
    )


def estimate_cpp_monthly(
    pensionable_earnings_ratio: float,
    start_age: int = 65,
    resolved: ResolvedParams | None = None,
) -> CPPEstimate:
    resolved = resolved or get_params(2026, "ON")
    params = resolved.params
    base = max(min(pensionable_earnings_ratio, 1.0), 0.0) * params.cpp_max_monthly_at_65
    return adjust_cpp_for_start_age(base, start_age)

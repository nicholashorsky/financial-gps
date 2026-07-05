"""Benefit election model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BenefitEnrollment:
    benefit_type: str
    elected_start_age: int
    estimated_monthly_amount: float | None = None
    source: str = "calculated"
    cpp_estimate_at_65: float | None = None
    oas_years_resident: int = 40

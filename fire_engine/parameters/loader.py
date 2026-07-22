"""Parameter loader with quarterly OAS/GIS resolution and effective_date support."""

from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date
from typing import Any

from fire_engine.parameters.cra_2026 import CRA2026Params, CRA_2026
from fire_engine.parameters.errors import UnsupportedTaxYearError


DEFAULT_PARAMETER_YEAR = 2026
YEAR_PARAMS_REGISTRY: dict[int, CRA2026Params] = {
    DEFAULT_PARAMETER_YEAR: CRA_2026,
}


@dataclass
class ResolvedParams:
    """CRA parameters resolved for a specific year, province, and effective date."""

    year: int
    province: str
    effective_date: date
    params: CRA2026Params
    parameter_year: int = DEFAULT_PARAMETER_YEAR

    @property
    def uses_fallback(self) -> bool:
        return self.year != self.parameter_year

    @property
    def tfsa_annual_limit(self) -> float:
        return self.params.tfsa_annual_limits.get(self.year, self.params.tfsa_annual_limit)

    @property
    def rrsp_max(self) -> float:
        return self.params.rrsp_annual_max.get(self.year, self.params.rrsp_max)

    @property
    def oas_max_monthly(self) -> float:
        """Return OAS max based on age band (default 65-74)."""
        return self.params.oas_max_monthly_65_74

    def oas_max_for_age(self, age: int) -> float:
        if age >= 75:
            return self.params.oas_max_monthly_75_plus
        return self.params.oas_max_monthly_65_74


# Quarterly OAS indexation factors (approximate — re-verify each quarter)
OAS_QUARTERLY_INDEX: dict[tuple[int, int], float] = {
    (2026, 1): 1.000,
    (2026, 2): 1.000,
    (2026, 3): 1.000,
    (2026, 4): 1.010,
}


def _quarter_from_date(effective_date: date) -> int:
    return (effective_date.month - 1) // 3 + 1


def get_params(
    year: int = DEFAULT_PARAMETER_YEAR,
    province: str = "ON",
    effective_date: date | None = None,
) -> ResolvedParams:
    """
    Load CRA parameters for the given year, province, and effective date.

    Supports quarterly OAS/GIS resolution via effective_date.
    Currently Ontario-only; Quebec returns a blocked flag via is_supported().
    """
    eff = effective_date or date(year, 7, 1)

    if province == "QC":
        raise ValueError("Quebec support coming soon.")

    if year not in YEAR_PARAMS_REGISTRY:
        raise UnsupportedTaxYearError(year, list(YEAR_PARAMS_REGISTRY))

    base = YEAR_PARAMS_REGISTRY[year]

    # Apply quarterly OAS indexation if applicable
    quarter = _quarter_from_date(eff)
    index_factor = OAS_QUARTERLY_INDEX.get((year, quarter), 1.0)

    if index_factor != 1.0:
        adjusted = CRA2026Params(
            oas_max_monthly_65_74=base.oas_max_monthly_65_74 * index_factor,
            oas_max_monthly_75_plus=base.oas_max_monthly_75_plus * index_factor,
        )
        return ResolvedParams(
            year=year,
            province=province,
            effective_date=eff,
            params=adjusted,
            parameter_year=year,
        )

    return ResolvedParams(
        year=year,
        province=province,
        effective_date=eff,
        params=base,
        parameter_year=year,
    )


def get_params_or_2026_fallback(
    year: int,
    province: str = "ON",
    effective_date: date | None = None,
) -> ResolvedParams:
    """Resolve a projection year, explicitly falling back to flat 2026 values."""
    try:
        return get_params(year, province, effective_date)
    except UnsupportedTaxYearError:
        requested_effective_date = effective_date or date(year, 7, 1)
        fallback_day = min(
            requested_effective_date.day,
            monthrange(DEFAULT_PARAMETER_YEAR, requested_effective_date.month)[1],
        )
        base_effective_date = date(
            DEFAULT_PARAMETER_YEAR,
            requested_effective_date.month,
            fallback_day,
        )
        resolved = get_params(DEFAULT_PARAMETER_YEAR, province, base_effective_date)
        return ResolvedParams(
            year=year,
            province=province,
            effective_date=requested_effective_date,
            params=resolved.params,
            parameter_year=DEFAULT_PARAMETER_YEAR,
        )


def is_province_supported(province: str) -> bool:
    return province != "QC"


def params_to_dict(resolved: ResolvedParams) -> dict[str, Any]:
    p = resolved.params
    return {
        "year": resolved.year,
        "parameter_year": resolved.parameter_year,
        "uses_fallback": resolved.uses_fallback,
        "province": resolved.province,
        "effective_date": resolved.effective_date.isoformat(),
        "tfsa_annual_limit": resolved.tfsa_annual_limit,
        "rrsp_max": resolved.rrsp_max,
        "cpp_ympe": p.cpp_ympe,
        "cpp2_yampe": p.cpp2_yampe,
        "oas_max_monthly_65_74": p.oas_max_monthly_65_74,
        "oas_max_monthly_75_plus": p.oas_max_monthly_75_plus,
        "oas_recovery_threshold": p.oas_recovery_threshold,
        "gis_earned_income_full_exempt": p.gis_earned_income_full_exempt,
        "gis_earned_income_partial_exempt": p.gis_earned_income_partial_exempt,
    }

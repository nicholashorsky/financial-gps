"""TFSA contribution room calculator."""

from __future__ import annotations

from dataclasses import dataclass

from fire_engine.parameters.loader import get_params


@dataclass(frozen=True)
class TFSARoomResult:
    snapshot_year: int
    available_room: float
    annual_limit: float
    warnings: list[str]


def calculate_tfsa_room(
    snapshot_year: int,
    prior_unused_room: float,
    prior_year_withdrawals: float = 0.0,
    ytd_contributions: float = 0.0,
    was_non_resident: bool = False,
) -> TFSARoomResult:
    params = get_params(snapshot_year, "ON").params
    annual_limit = 0.0 if was_non_resident else params.tfsa_annual_limits.get(snapshot_year, params.tfsa_annual_limit)
    available = prior_unused_room + annual_limit + prior_year_withdrawals - ytd_contributions
    warnings = []
    if available < 0:
        warnings.append("TFSA over-contribution risk.")
    if was_non_resident:
        warnings.append("No TFSA room accrues while non-resident.")
    return TFSARoomResult(snapshot_year, round(available, 2), annual_limit, warnings)

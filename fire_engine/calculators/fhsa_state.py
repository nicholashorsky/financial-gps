"""FHSA room and lifecycle calculator."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from fire_engine.parameters.loader import get_params


@dataclass(frozen=True)
class FHSAStateResult:
    snapshot_year: int
    annual_room: float
    carryforward_room: float
    available_room: float
    remaining_lifetime_room: float
    years_until_expiry: int | None
    warnings: list[str]


def calculate_fhsa_state(
    snapshot_year: int,
    open_date: date | None,
    carryforward_room: float = 0.0,
    ytd_contributions: float = 0.0,
    lifetime_contributions: float = 0.0,
    is_first_time_buyer: bool = True,
) -> FHSAStateResult:
    params = get_params(snapshot_year, "ON").params
    annual_room = params.fhsa_annual
    accrued_carryforward = min(carryforward_room, annual_room)
    available_room = max(annual_room + accrued_carryforward - ytd_contributions, 0.0)
    remaining_lifetime_room = max(params.fhsa_lifetime - lifetime_contributions, 0.0)

    years_until_expiry = None
    warnings: list[str] = []
    if open_date is not None:
        years_open = max(snapshot_year - open_date.year, 0)
        years_until_expiry = max(15 - years_open, 0)
        if years_until_expiry <= 2:
            warnings.append("FHSA expiry approaching.")
    if not is_first_time_buyer:
        warnings.append("FHSA requires first-time home buyer eligibility.")
    return FHSAStateResult(
        snapshot_year=snapshot_year,
        annual_room=annual_room,
        carryforward_room=accrued_carryforward,
        available_room=round(min(available_room, remaining_lifetime_room), 2),
        remaining_lifetime_room=round(remaining_lifetime_room, 2),
        years_until_expiry=years_until_expiry,
        warnings=warnings,
    )

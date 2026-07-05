"""RRSP deduction room calculator."""

from __future__ import annotations

from dataclasses import dataclass

from fire_engine.parameters.loader import get_params


@dataclass(frozen=True)
class RRSPRoomResult:
    snapshot_year: int
    deduction_limit: float
    annual_rrsp_max: float
    contribution_room_after_ytd: float


def calculate_rrsp_room(
    snapshot_year: int,
    prior_unused_room: float,
    prior_year_earned_income: float,
    pension_adjustment: float = 0.0,
    par_amount: float = 0.0,
    pspa_amount: float = 0.0,
    ytd_contributions: float = 0.0,
) -> RRSPRoomResult:
    annual_max = get_params(snapshot_year, "ON").rrsp_max
    earned_income_room = min(prior_year_earned_income * 0.18, annual_max)
    deduction_limit = prior_unused_room + earned_income_room - pension_adjustment + par_amount - pspa_amount
    after_ytd = deduction_limit - ytd_contributions
    return RRSPRoomResult(snapshot_year, round(deduction_limit, 2), annual_max, round(after_ytd, 2))

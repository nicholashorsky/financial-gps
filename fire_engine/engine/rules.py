"""Rule registry for projection warnings."""

from __future__ import annotations

from fire_engine.models.household import Household


def evaluate_rules(
    year: int,
    household: Household,
    projected_income: float,
    *,
    rrif_converted: bool = False,
    rrif_minimum_withdrawal: float = 0.0,
) -> list[str]:
    rules: list[str] = []
    age = household.primary.age_in_year(year)
    if 69 <= age <= 70:
        rules.append("RRSP age-71 approaching")
    if rrif_converted:
        rules.append("RRSP converted to RRIF this year")
    if rrif_minimum_withdrawal > 0:
        rules.append("RRIF minimum withdrawal in effect")
    if projected_income >= 80323:
        rules.append("OAS threshold proximity")
    if household.primary.is_quebec:
        rules.append("Quebec support coming soon")
    return rules

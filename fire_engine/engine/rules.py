"""Rule registry for projection warnings."""

from __future__ import annotations

from fire_engine.models.household import Household


def evaluate_rules(year: int, household: Household, projected_income: float) -> list[str]:
    rules: list[str] = []
    age = household.primary.age_in_year(year)
    if age >= 69 and age <= 71:
        rules.append("RRSP age-71 approaching")
    if projected_income >= 80323:
        rules.append("OAS threshold proximity")
    if household.primary.is_quebec:
        rules.append("Quebec support coming soon")
    return rules

"""Person model for FIRE calculations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Person:
    name: str
    date_of_birth: date
    province: str = "ON"
    years_in_canada_post_18: int = 40
    is_canadian_resident: bool = True
    is_quebec: bool = False

    def age_in_year(self, year: int) -> int:
        return year - self.date_of_birth.year

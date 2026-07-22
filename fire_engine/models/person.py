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

    def age_at_start_of_year(self, year: int) -> int:
        """Return age on January 1, used for prescribed RRIF factors."""
        age = year - self.date_of_birth.year
        if (self.date_of_birth.month, self.date_of_birth.day) > (1, 1):
            age -= 1
        return age

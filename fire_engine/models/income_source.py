"""Income source model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IncomeSource:
    source_type: str
    annual_amount: float
    income_character: str = "employment"
    start_year: int | None = None
    end_year: int | None = None
    inflation_rate: float = 0.03
    is_pensionable: bool = True

    def amount_for_year(self, year: int) -> float:
        if self.start_year and year < self.start_year:
            return 0.0
        if self.end_year and year > self.end_year:
            return 0.0
        start = self.start_year or year
        return self.annual_amount * ((1 + self.inflation_rate) ** max(year - start, 0))

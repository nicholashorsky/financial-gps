"""Investment account model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass
class InvestmentAccount:
    account_type: str
    current_balance: float
    opened_date: date | None = None
    institution: str | None = None
    beneficiary_type: str | None = None
    annual_return: float = 0.05
    rrif_conversion_year: int | None = None

    def grow_one_year(self) -> None:
        self.current_balance *= 1 + self.annual_return

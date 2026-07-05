"""Tax result model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaxResult:
    taxable_income: float
    federal_tax: float
    provincial_tax: float
    oas_recovery_tax: float = 0.0

    @property
    def total_tax(self) -> float:
        return self.federal_tax + self.provincial_tax + self.oas_recovery_tax

    @property
    def effective_rate(self) -> float:
        if self.taxable_income <= 0:
            return 0.0
        return self.total_tax / self.taxable_income

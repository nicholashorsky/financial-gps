"""Errors raised while resolving CRA calculation parameters."""

from __future__ import annotations


class UnsupportedTaxYearError(ValueError):
    """Raised when verified CRA parameters are unavailable for a year."""

    def __init__(self, year: int, supported_years: list[int]) -> None:
        self.year = year
        self.supported_years = sorted(supported_years)
        supported = ", ".join(str(item) for item in self.supported_years)
        super().__init__(
            f"No verified CRA parameters are loaded for {year}. "
            f"Supported years: {supported}."
        )

"""RRIF prescribed-factor and minimum-withdrawal calculations."""

from __future__ import annotations

from dataclasses import dataclass


RRIF_CONVERSION_AGE = 71
RRIF_MINIMUM_START_AGE = 72

# Income Tax Regulations, C.R.C., c. 945, s. 7308(4), current May 26, 2026:
# https://laws-lois.justice.gc.ca/eng/regulations/C.R.C.,_c._945/section-7308.html
RRIF_PRESCRIBED_FACTORS: dict[int, float] = {
    71: 0.0528,
    72: 0.0540,
    73: 0.0553,
    74: 0.0567,
    75: 0.0582,
    76: 0.0598,
    77: 0.0617,
    78: 0.0636,
    79: 0.0658,
    80: 0.0682,
    81: 0.0708,
    82: 0.0738,
    83: 0.0771,
    84: 0.0808,
    85: 0.0851,
    86: 0.0899,
    87: 0.0955,
    88: 0.1021,
    89: 0.1099,
    90: 0.1192,
    91: 0.1306,
    92: 0.1449,
    93: 0.1634,
    94: 0.1879,
}
RRIF_FACTOR_95_PLUS = 0.20


@dataclass(frozen=True)
class RRIFMinimumResult:
    age: int
    factor: float
    opening_balance: float
    minimum_withdrawal: float


def rrif_prescribed_factor(age: int) -> float:
    """Return the standard prescribed factor for a non-qualifying RRIF."""
    if age < RRIF_CONVERSION_AGE:
        return round(1 / (90 - age), 6)
    if age >= 95:
        return RRIF_FACTOR_95_PLUS
    return RRIF_PRESCRIBED_FACTORS[age]


def calculate_rrif_minimum(age: int, opening_balance: float) -> RRIFMinimumResult:
    """Calculate the annual minimum from the balance at the start of the year."""
    balance = max(opening_balance, 0.0)
    factor = rrif_prescribed_factor(age)
    minimum = round(balance * factor, 2)
    return RRIFMinimumResult(
        age=age,
        factor=factor,
        opening_balance=round(balance, 2),
        minimum_withdrawal=minimum,
    )

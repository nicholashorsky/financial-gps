"""CRA tax and benefit parameters for 2026 (verified from T4032-ON)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TaxBracket:
    income_from: float
    income_to: float | None
    rate: float
    constant: float


@dataclass(frozen=True)
class CRA2026Params:
    year: int = 2026
    province: str = "ON"

    # Federal tax brackets (Rate × Income − K)
    federal_brackets: tuple[TaxBracket, ...] = (
        TaxBracket(0, 58523, 0.14, 0),
        TaxBracket(58523, 117045, 0.205, 3804),
        TaxBracket(117045, 181440, 0.26, 10241),
        TaxBracket(181440, 258482, 0.29, 15685),
        TaxBracket(258482, None, 0.33, 26024),
    )

    # Federal BPA
    federal_bpa_max: float = 16452
    federal_bpa_floor: float = 14829
    federal_bpa_phase_out_start: float = 181440
    federal_bpa_phase_out_end: float = 258482
    federal_lowest_rate: float = 0.14

    # Ontario provincial brackets (Rate × Income − KP)
    provincial_brackets: tuple[TaxBracket, ...] = (
        TaxBracket(0, 53891, 0.0505, 0),
        TaxBracket(53891, 107785, 0.0915, 2210),
        TaxBracket(107785, 150000, 0.1116, 4376),
        TaxBracket(150000, 220000, 0.1216, 5876),
        TaxBracket(220000, None, 0.1316, 8076),
    )

    ontario_bpa: float = 12989
    ontario_surtax_tier1_threshold: float = 5818
    ontario_surtax_tier1_rate: float = 0.20
    ontario_surtax_tier2_threshold: float = 7446
    ontario_surtax_tier2_rate: float = 0.36
    ontario_low_income_reduction_base: float = 300

    # Ontario health premium bands (taxable income thresholds)
    ontario_health_premium_bands: tuple[tuple[float, float, float], ...] = (
        (0, 20000, 0),
        (20000, 36000, 300),
        (36000, 48000, 450),
        (48000, 72000, 600),
        (72000, 200000, 750),
        (200000, None, 900),
    )

    # Account limits
    tfsa_annual_limit: float = 7000
    tfsa_cumulative_since_2009: float = 109000
    rrsp_max: float = 33810
    fhsa_annual: float = 8000
    fhsa_lifetime: float = 40000

    # CPP
    cpp_ympe: float = 74600
    cpp2_yampe: float = 85000
    cpp_employee_rate: float = 0.0595
    cpp_self_employed_rate: float = 0.119
    cpp2_rate: float = 0.04
    cpp_max_monthly_at_65: float = 1364.60  # approximate 2026 max

    # OAS (Q3 2026 quarterly indexed)
    oas_max_monthly_65_74: float = 751.97
    oas_max_monthly_75_plus: float = 827.17
    oas_recovery_threshold: float = 95323
    oas_deferral_increase_per_month: float = 0.006  # 0.6% per month deferred

    # GIS
    gis_earned_income_full_exempt: float = 5000
    gis_earned_income_partial_exempt: float = 10000
    gis_single_threshold: float = 22008  # approximate 2026
    gis_couple_threshold: float = 29040  # approximate 2026

    # Investment income
    capital_gains_inclusion_rate: float = 0.50
    eligible_dividend_gross_up: float = 0.38
    non_eligible_dividend_gross_up: float = 0.15

    # TFSA limits by year (for room calculations)
    tfsa_annual_limits: dict[int, float] = field(default_factory=lambda: {
        2009: 5000, 2010: 5000, 2011: 5000, 2012: 5000, 2013: 5500,
        2014: 5500, 2015: 10000, 2016: 5500, 2017: 5500, 2018: 5500,
        2019: 6000, 2020: 6000, 2021: 6000, 2022: 6000, 2023: 6500,
        2024: 7000, 2025: 7000, 2026: 7000,
    })

    # RRSP max by year
    rrsp_annual_max: dict[int, float] = field(default_factory=lambda: {
        2024: 31560, 2025: 32490, 2026: 33810,
    })

    # CRA regression test cases (gold standard)
    regression_cases: tuple[tuple[float, float, float, float], ...] = (
        (62798.84, 5957.85, 3264.26, 9222.11),
        (79872.00, 9406.39, 4957.90, 14364.29),
    )


CRA_2026 = CRA2026Params()

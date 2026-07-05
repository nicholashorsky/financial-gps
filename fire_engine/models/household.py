"""Household model for deterministic FIRE projection."""

from __future__ import annotations

from dataclasses import dataclass, field

from fire_engine.models.benefit_enrollment import BenefitEnrollment
from fire_engine.models.income_source import IncomeSource
from fire_engine.models.investment_account import InvestmentAccount
from fire_engine.models.person import Person


@dataclass
class Household:
    primary: Person
    income_sources: list[IncomeSource] = field(default_factory=list)
    accounts: list[InvestmentAccount] = field(default_factory=list)
    benefits: list[BenefitEnrollment] = field(default_factory=list)
    annual_spending: float = 60000
    spending_inflation: float = 0.025
    start_year: int = 2026

"""Shared dataclasses and DTOs."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any


@dataclass
class User:
    id: int
    email: str
    name: str | None = None
    created_at: str | None = None


@dataclass
class BridgeResult:
    income_synced: bool = False
    categories_synced: int = 0
    fields_updated: int = 0
    fields_preserved: int = 0
    warnings: list[str] = field(default_factory=list)


@dataclass
class Transaction:
    id: int
    user_id: int
    account_id: int | None
    date: date
    description: str
    amount: float
    category: str | None = None
    transaction_type: str = "expense"
    is_excluded: bool = False
    source: str = "csv_import"


@dataclass
class FireProfile:
    id: str
    user_id: int
    province: str | None = None
    date_of_birth: date | None = None
    fire_variant: str | None = None
    target_retire_year: int | None = None
    spending_floor: float | None = None
    spending_ceiling: float | None = None


@dataclass
class DataQualityWarning:
    code: str
    message: str
    severity: str = "warning"  # info | warning | error

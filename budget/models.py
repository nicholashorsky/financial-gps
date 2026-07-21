"""Budget layer dataclasses."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass
class ParsedTransaction:
    date: date
    description: str
    amount: float
    raw_description: str = ""
    account_hint: str = ""
    account_type_hint: str = ""  # chequing | credit | savings
    source_row: int = 0


@dataclass
class DetectedAccount:
    key: str  # stable id from parser (type + last4)
    account_type: str
    account_number_hint: str
    suggested_name: str
    transaction_count: int = 0


@dataclass
class ParseResult:
    format_name: str
    transactions: list[ParsedTransaction] = field(default_factory=list)
    accounts: list[DetectedAccount] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    raw_columns: list[str] = field(default_factory=list)
    needs_column_mapping: bool = False


@dataclass
class CategorizedTransaction:
    date: date
    description: str
    amount: float
    category: str
    transaction_type: str
    raw_description: str = ""
    account_key: str = ""
    import_hash: str = ""


@dataclass
class TransferMatch:
    out_txn_index: int
    in_txn_index: int
    confidence: float
    match_reason: str


@dataclass
class ImportResult:
    batch_id: int | None = None
    imported: int = 0
    skipped_duplicates: int = 0
    transfers_matched: int = 0
    bridge_fields_updated: int = 0
    bridge_fields_preserved: int = 0
    ghost_accounts: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

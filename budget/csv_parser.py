"""RBC and generic CSV parser with multi-account detection."""

from __future__ import annotations

import hashlib
import io
import re
from datetime import date, datetime
from typing import Any

import pandas as pd

from budget.models import DetectedAccount, ParsedTransaction, ParseResult

RBC_MULTI_COLUMNS = {
    "account type",
    "account number",
    "transaction date",
    "cheque number",
    "description 1",
    "description 2",
    "cad$",
    "usd$",
}

RBC_CC_COLUMNS = {
    "transaction date",
    "posting date",
    "activity",
    "description",
    "amount (cad)",
    "amount (usd)",
}

RBC_CC_ALT = {"transaction date", "description", "amount"}

DATE_FORMATS = (
    "%Y-%m-%d",
    "%m/%d/%Y",
    "%d/%m/%Y",
    "%Y/%m/%d",
    "%m-%d-%Y",
    "%d-%m-%Y",
    "%b %d, %Y",
    "%B %d, %Y",
)


def _normalize_columns(cols: list[str]) -> list[str]:
    return [str(c).strip().lower() for c in cols]


def _parse_date(value: Any) -> date | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, datetime):
        return value.date()
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    try:
        return pd.to_datetime(text, dayfirst=False).date()
    except Exception:
        return None


def _parse_amount(value: Any) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip().replace(",", "").replace("$", "")
    if not text or text.lower() == "nan":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _combine_description(*parts: Any) -> str:
    bits = []
    for p in parts:
        if p is None or (isinstance(p, float) and pd.isna(p)):
            continue
        s = str(p).strip()
        if s and s.lower() != "nan":
            bits.append(s)
    return " — ".join(bits) if len(bits) > 1 else (bits[0] if bits else "")


def _account_type_from_hint(account_type: str) -> str:
    t = account_type.lower()
    if "visa" in t or "mastercard" in t or "credit" in t or "card" in t:
        return "credit"
    if "saving" in t:
        return "savings"
    return "chequing"


def _account_key(account_type: str, account_number: str) -> str:
    digits = re.sub(r"\D", "", account_number)[-4:] or "0000"
    return f"{_account_type_from_hint(account_type)}:{digits}"


def _read_csv(content: bytes | str) -> pd.DataFrame:
    if isinstance(content, bytes):
        for encoding in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
            try:
                text = content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            text = content.decode("utf-8", errors="replace")
    else:
        text = content

    try:
        df = pd.read_csv(io.StringIO(text), dtype=str, keep_default_na=False)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()
    df.columns = [str(c).strip() for c in df.columns]
    return df


def detect_format(df: pd.DataFrame) -> str:
    cols = set(_normalize_columns(list(df.columns)))
    if RBC_MULTI_COLUMNS.issubset(cols):
        return "rbc_multi"
    if RBC_CC_COLUMNS.issubset(cols):
        return "rbc_credit_card"
    if RBC_CC_ALT.issubset(cols) and "posting date" not in cols:
        if any("visa" in c or "credit" in c for c in cols):
            return "rbc_credit_card"
        if len(cols) <= 5:
            return "generic_simple"
    return "unknown"


def _parse_rbc_multi(df: pd.DataFrame) -> ParseResult:
    col_map = {c.lower(): c for c in df.columns}
    transactions: list[ParsedTransaction] = []
    account_counts: dict[str, int] = {}
    account_meta: dict[str, tuple[str, str]] = {}

    for idx, row in df.iterrows():
        acct_type = str(row.get(col_map["account type"], "")).strip()
        acct_num = str(row.get(col_map["account number"], "")).strip()
        txn_date = _parse_date(row.get(col_map["transaction date"]))
        desc = _combine_description(
            row.get(col_map["description 1"]),
            row.get(col_map["description 2"]),
        )
        amount = _parse_amount(row.get(col_map["cad$"]))
        if amount is None:
            amount = _parse_amount(row.get(col_map["usd$"]))
        if txn_date is None or amount is None or not desc:
            continue

        key = _account_key(acct_type, acct_num)
        acct_type_norm = _account_type_from_hint(acct_type)
        account_counts[key] = account_counts.get(key, 0) + 1
        account_meta[key] = (acct_type_norm, acct_num)

        transactions.append(
            ParsedTransaction(
                date=txn_date,
                description=desc,
                amount=amount,
                raw_description=desc,
                account_hint=key,
                account_type_hint=acct_type_norm,
                source_row=int(idx) + 2,
            )
        )

    accounts = _build_detected_accounts(account_counts, account_meta)
    skipped_invalid = len(df) - len(transactions)
    warnings = _invalid_row_warnings(skipped_invalid)
    return ParseResult(
        format_name="rbc_multi",
        transactions=transactions,
        accounts=accounts,
        warnings=warnings,
        skipped_invalid=skipped_invalid,
    )


def _parse_rbc_credit_card(df: pd.DataFrame) -> ParseResult:
    col_map = {c.lower(): c for c in df.columns}
    date_col = col_map.get("transaction date") or col_map.get("date")
    desc_col = col_map.get("description") or col_map.get("activity")
    amount_col = (
        col_map.get("amount (cad)")
        or col_map.get("amount")
        or col_map.get("cad$")
    )

    transactions: list[ParsedTransaction] = []
    for idx, row in df.iterrows():
        txn_date = _parse_date(row.get(date_col)) if date_col else None
        desc = str(row.get(desc_col, "")).strip() if desc_col else ""
        amount = _parse_amount(row.get(amount_col)) if amount_col else None
        if txn_date is None or amount is None or not desc:
            continue

        # RBC CC: charges positive, payments negative — normalize to expense negative
        desc_upper = desc.upper()
        if "PAYMENT RECEIVED" in desc_upper or "PAYMENT - THANK YOU" in desc_upper:
            txn_type_amount = abs(amount)  # payment in = positive on CC statement
        else:
            txn_type_amount = -abs(amount)  # purchase = expense

        transactions.append(
            ParsedTransaction(
                date=txn_date,
                description=desc,
                amount=txn_type_amount,
                raw_description=desc,
                account_hint="credit:0000",
                account_type_hint="credit",
                source_row=int(idx) + 2,
            )
        )

    accounts = [
        DetectedAccount(
            key="credit:0000",
            account_type="credit",
            account_number_hint="****",
            suggested_name="RBC Credit Card",
            transaction_count=len(transactions),
        )
    ]
    skipped_invalid = len(df) - len(transactions)
    warnings = _invalid_row_warnings(skipped_invalid)
    return ParseResult(
        format_name="rbc_credit_card",
        transactions=transactions,
        accounts=accounts,
        warnings=warnings,
        skipped_invalid=skipped_invalid,
    )


def _parse_generic_simple(df: pd.DataFrame, column_map: dict[str, str] | None = None) -> ParseResult:
    col_map = column_map or _guess_simple_columns(df)
    if not col_map:
        return ParseResult(
            format_name="unknown",
            raw_columns=list(df.columns),
            needs_column_mapping=True,
        )

    transactions: list[ParsedTransaction] = []
    for idx, row in df.iterrows():
        txn_date = _parse_date(row.get(col_map["date"]))
        desc = str(row.get(col_map["description"], "")).strip()
        amount = _parse_amount(row.get(col_map["amount"]))
        if txn_date is None or amount is None or not desc:
            continue
        transactions.append(
            ParsedTransaction(
                date=txn_date,
                description=desc,
                amount=amount,
                raw_description=desc,
                account_hint="chequing:0000",
                account_type_hint="chequing",
                source_row=int(idx) + 2,
            )
        )

    accounts = [
        DetectedAccount(
            key="chequing:0000",
            account_type="chequing",
            account_number_hint="****",
            suggested_name="Imported Account",
            transaction_count=len(transactions),
        )
    ]
    skipped_invalid = len(df) - len(transactions)
    warnings = _invalid_row_warnings(skipped_invalid)
    return ParseResult(
        format_name="generic_simple",
        transactions=transactions,
        accounts=accounts,
        warnings=warnings,
        skipped_invalid=skipped_invalid,
    )


def _invalid_row_warnings(invalid_rows: int) -> list[str]:
    if invalid_rows <= 0:
        return []
    return [
        f"Skipped {invalid_rows} invalid row(s). Each imported row needs a valid date, description, and amount."
    ]


def _guess_simple_columns(df: pd.DataFrame) -> dict[str, str] | None:
    lower = {c.lower(): c for c in df.columns}
    date_candidates = ["transaction date", "date", "trans date", "posting date"]
    desc_candidates = ["description", "description 1", "memo", "details", "activity"]
    amount_candidates = ["amount", "cad$", "amount (cad)", "debit", "credit"]

    date_col = next((lower[c] for c in date_candidates if c in lower), None)
    desc_col = next((lower[c] for c in desc_candidates if c in lower), None)
    amount_col = next((lower[c] for c in amount_candidates if c in lower), None)

    if date_col and desc_col and amount_col:
        return {"date": date_col, "description": desc_col, "amount": amount_col}
    return None


def _build_detected_accounts(
    account_counts: dict[str, int],
    account_meta: dict[str, tuple[str, str]],
) -> list[DetectedAccount]:
    accounts = []
    for key, count in account_counts.items():
        acct_type, acct_num = account_meta[key]
        last4 = re.sub(r"\D", "", acct_num)[-4:] or "****"
        type_label = {"credit": "Credit Card", "chequing": "Chequing", "savings": "Savings"}.get(
            acct_type, "Account"
        )
        accounts.append(
            DetectedAccount(
                key=key,
                account_type=acct_type,
                account_number_hint=f"****{last4}",
                suggested_name=f"RBC {type_label} {last4}",
                transaction_count=count,
            )
        )
    return sorted(accounts, key=lambda a: a.key)


def parse_csv(
    content: bytes | str,
    column_map: dict[str, str] | None = None,
) -> ParseResult:
    """Parse bank CSV content. Returns transactions and detected accounts."""
    df = _read_csv(content)
    if df.empty:
        return ParseResult(format_name="empty", warnings=["CSV file is empty."])

    fmt = detect_format(df)
    if fmt == "rbc_multi":
        return _parse_rbc_multi(df)
    if fmt == "rbc_credit_card":
        return _parse_rbc_credit_card(df)
    if fmt == "generic_simple":
        return _parse_generic_simple(df, column_map)
    if column_map:
        return _parse_generic_simple(df, column_map)

    guessed = _guess_simple_columns(df)
    if guessed:
        return _parse_generic_simple(df, guessed)

    return ParseResult(
        format_name="unknown",
        raw_columns=list(df.columns),
        needs_column_mapping=True,
        warnings=["Could not detect CSV format. Please map columns manually."],
    )


def preview_csv(content: bytes | str, max_rows: int = 10) -> pd.DataFrame:
    df = _read_csv(content)
    return df.head(max_rows)


def make_import_hash(account_id: int, txn_date: date, amount: float, description: str) -> str:
    d = txn_date.isoformat() if isinstance(txn_date, date) else str(txn_date)
    payload = f"{account_id}|{d}|{amount:.2f}|{description.strip().lower()}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

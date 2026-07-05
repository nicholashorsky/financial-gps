"""Credit card payment transfer detection and matching."""

from __future__ import annotations

import re
from datetime import timedelta

from budget.models import CategorizedTransaction, TransferMatch

CC_PAYMENT_PATTERNS_OUT = (
    r"payment to rbc",
    r"rbc royal bank visa",
    r"visa payment",
    r"mastercard payment",
    r"credit card payment",
    r"bill payment.*visa",
    r"bill payment.*mastercard",
    r"paiement.*visa",
)

CC_PAYMENT_PATTERNS_IN = (
    r"payment received",
    r"payment - thank you",
    r"payment thank you",
    r"paiement recu",
)


def _normalize_desc(desc: str) -> str:
    return desc.lower().strip()


def _matches_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(p, text) for p in patterns)


def is_cc_payment_out(txn: CategorizedTransaction) -> bool:
    desc = _normalize_desc(txn.description)
    return txn.amount < 0 and _matches_any(desc, CC_PAYMENT_PATTERNS_OUT)


def is_cc_payment_in(txn: CategorizedTransaction) -> bool:
    desc = _normalize_desc(txn.description)
    return txn.amount > 0 and _matches_any(desc, CC_PAYMENT_PATTERNS_IN)


def _amounts_match(a: float, b: float, tolerance: float = 0.01) -> bool:
    return abs(abs(a) - abs(b)) <= tolerance


def _dates_close(d1, d2, max_days: int = 5) -> bool:
    return abs((d1 - d2).days) <= max_days


def detect_transfers(
    transactions: list[CategorizedTransaction],
    account_types: dict[str, str] | None = None,
) -> list[TransferMatch]:
    """
    Match chequing CC payments with credit card payment-received lines.
    account_types maps account_key -> chequing|credit|savings
    """
    account_types = account_types or {}
    matches: list[TransferMatch] = []
    matched_indices: set[int] = set()

    outs = []
    ins = []
    for i, txn in enumerate(transactions):
        acct_type = account_types.get(txn.account_key, "")
        if acct_type == "chequing" or (not acct_type and txn.amount < 0):
            if is_cc_payment_out(txn):
                outs.append(i)
        if acct_type == "credit" or (not acct_type and txn.amount > 0):
            if is_cc_payment_in(txn):
                ins.append(i)

    for out_idx in outs:
        out_txn = transactions[out_idx]
        best_match: TransferMatch | None = None
        for in_idx in ins:
            if in_idx in matched_indices:
                continue
            in_txn = transactions[in_idx]
            if not _amounts_match(out_txn.amount, in_txn.amount):
                continue
            if not _dates_close(out_txn.date, in_txn.date):
                continue
            confidence = 0.9 if out_txn.date == in_txn.date else 0.75
            candidate = TransferMatch(
                out_txn_index=out_idx,
                in_txn_index=in_idx,
                confidence=confidence,
                match_reason="CC payment amount and date match",
            )
            if best_match is None or candidate.confidence > best_match.confidence:
                best_match = candidate

        if best_match:
            matches.append(best_match)
            matched_indices.add(best_match.out_txn_index)
            matched_indices.add(best_match.in_txn_index)

    return matches


def apply_transfer_matches(
    transactions: list[CategorizedTransaction],
    matches: list[TransferMatch],
) -> list[CategorizedTransaction]:
    """Mark matched transfers as excluded from spending totals."""
    excluded_indices = set()
    for m in matches:
        excluded_indices.add(m.out_txn_index)
        excluded_indices.add(m.in_txn_index)

    updated = []
    for i, txn in enumerate(transactions):
        if i in excluded_indices:
            txn = CategorizedTransaction(
                date=txn.date,
                description=txn.description,
                amount=txn.amount,
                category="Transfer",
                transaction_type="cc_payment" if txn.amount < 0 else "transfer_in",
                raw_description=txn.raw_description,
                account_key=txn.account_key,
                import_hash=txn.import_hash,
            )
        updated.append(txn)
    return updated

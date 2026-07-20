"""CSV import service for the budget layer."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Mapping

from budget.categorizer import categorize_transactions
from budget.csv_parser import make_import_hash, parse_csv
from budget.models import CategorizedTransaction, DetectedAccount, ImportResult
from budget.transfer_detector import apply_transfer_matches, detect_transfers
from shared.utils import utc_now_iso


@dataclass
class ImportSummary:
    """Lightweight dashboard data for spending/home screens."""

    imported_count: int
    transaction_count: int
    spending_total: float
    income_total: float
    account_count: int
    recent_transactions: list[sqlite3.Row]
    spending_by_category: list[sqlite3.Row]


def _account_label(account: DetectedAccount, override: str | None = None) -> str:
    name = (override or "").strip()
    return name or account.suggested_name or f"Imported {account.account_type.title()}"


def _get_account_by_key(
    conn: sqlite3.Connection,
    user_id: int,
    account_key: str,
) -> sqlite3.Row | None:
    return conn.execute(
        """
        SELECT *
        FROM accounts
        WHERE user_id = ? AND account_key = ?
        """,
        (user_id, account_key),
    ).fetchone()


def upsert_account(
    conn: sqlite3.Connection,
    user_id: int,
    account: DetectedAccount,
    display_name: str | None = None,
) -> int:
    """Create or update an imported account record and return its id."""

    existing = _get_account_by_key(conn, user_id, account.key)
    name = _account_label(account, display_name)
    if existing:
        conn.execute(
            """
            UPDATE accounts
            SET name = ?, type = ?, is_imported = 1, account_number_hint = ?, last_imported_at = ?
            WHERE id = ?
            """,
            (name, account.account_type, account.account_number_hint, utc_now_iso(), existing["id"]),
        )
        return int(existing["id"])

    cursor = conn.execute(
        """
        INSERT INTO accounts (
            user_id, name, type, balance, is_imported,
            account_key, account_number_hint, last_imported_at
        )
        VALUES (?, ?, ?, 0, 1, ?, ?, ?)
        """,
        (user_id, name, account.account_type, account.key, account.account_number_hint, utc_now_iso()),
    )
    return int(cursor.lastrowid)


def _resolve_account_id(
    account_ids: dict[str, int],
    txn_account_key: str,
    fallback_account_id: int | None = None,
) -> int | None:
    if txn_account_key and txn_account_key in account_ids:
        return account_ids[txn_account_key]
    return fallback_account_id


def _insert_transaction(
    conn: sqlite3.Connection,
    user_id: int,
    account_id: int,
    txn: CategorizedTransaction,
) -> tuple[int, bool]:
    import_hash = make_import_hash(account_id, txn.date, txn.amount, txn.description)
    existing = conn.execute(
        "SELECT id FROM transactions WHERE import_hash = ?",
        (import_hash,),
    ).fetchone()
    if existing:
        return int(existing["id"]), False

    cursor = conn.execute(
        """
        INSERT INTO transactions (
            user_id, account_id, date, description, amount, category,
            transaction_type, is_recurring, is_excluded, source,
            raw_description, import_hash
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, 'csv_import', ?, ?)
        """,
        (
            user_id,
            account_id,
            txn.date.isoformat(),
            txn.description,
            txn.amount,
            txn.category,
            txn.transaction_type,
            txn.raw_description,
            import_hash,
        ),
    )
    return int(cursor.lastrowid), True


def import_csv_transactions(
    conn: sqlite3.Connection,
    user_id: int,
    content: bytes | str,
    *,
    column_map: dict[str, str] | None = None,
    account_name_overrides: Mapping[str, str] | None = None,
) -> tuple[ImportResult, list[CategorizedTransaction]]:
    """
    Parse, categorize, detect transfers, and persist imported transactions.

    Returns the import summary plus the categorized transaction list used by the UI.
    """

    account_name_overrides = dict(account_name_overrides or {})
    parse_result = parse_csv(content, column_map=column_map)
    result = ImportResult(warnings=list(parse_result.warnings))

    if parse_result.needs_column_mapping:
        result.warnings.append("Map the CSV columns before importing.")
        return result, []

    categorized = categorize_transactions(parse_result.transactions, conn=conn, user_id=user_id)
    account_types = {
        txn.account_key: txn.account_key.split(":", 1)[0] if txn.account_key else ""
        for txn in categorized
    }
    matches = detect_transfers(categorized, account_types=account_types)
    categorized = apply_transfer_matches(categorized, matches)

    account_ids: dict[str, int] = {}
    ghost_accounts: list[str] = []
    for account in parse_result.accounts:
        override = account_name_overrides.get(account.key)
        account_id = upsert_account(conn, user_id, account, override)
        account_ids[account.key] = account_id
        if not override:
            ghost_accounts.append(_account_label(account))

    fallback_account_id = next(iter(account_ids.values()), None)
    inserted_ids: list[int | None] = []
    imported_count = 0
    skipped_duplicates = 0

    for txn in categorized:
        account_id = _resolve_account_id(account_ids, txn.account_key, fallback_account_id)
        if account_id is None:
            result.warnings.append(f"Skipped '{txn.description}' because no account could be resolved.")
            inserted_ids.append(None)
            continue

        inserted_id, is_new = _insert_transaction(conn, user_id, account_id, txn)
        inserted_ids.append(inserted_id)
        if is_new:
            imported_count += 1
        else:
            skipped_duplicates += 1

    transfers_matched = 0
    for match in matches:
        out_id = inserted_ids[match.out_txn_index]
        in_id = inserted_ids[match.in_txn_index]
        if out_id is None or in_id is None:
            continue
        conn.execute(
            "UPDATE transactions SET transfer_match_id = ? WHERE id = ?",
            (in_id, out_id),
        )
        conn.execute(
            "UPDATE transactions SET transfer_match_id = ? WHERE id = ?",
            (out_id, in_id),
        )
        conn.execute(
            """
            UPDATE transactions
            SET is_excluded = 1,
                category = 'Transfer',
                transaction_type = CASE WHEN amount < 0 THEN 'cc_payment' ELSE 'transfer_in' END
            WHERE id IN (?, ?)
            """,
            (out_id, in_id),
        )
        transfers_matched += 1

    conn.commit()

    result.imported = imported_count
    result.skipped_duplicates = skipped_duplicates
    result.transfers_matched = transfers_matched
    result.ghost_accounts = ghost_accounts
    if ghost_accounts:
        result.warnings.append(
            f"Detected {len(ghost_accounts)} new account(s). Review the suggested names before the next import."
        )
    try:
        from bridge.data_bridge import sync_fire_defaults

        bridge_result = sync_fire_defaults(conn, user_id)
        result.bridge_fields_updated = bridge_result.fields_updated
        result.bridge_fields_preserved = bridge_result.fields_preserved
        result.warnings.extend(bridge_result.warnings)
    except Exception as exc:  # pragma: no cover - bridge is best-effort for imports
        result.warnings.append(f"Bridge sync skipped: {exc}")
    return result, categorized


def get_spending_summary(conn: sqlite3.Connection, user_id: int, limit: int = 10) -> ImportSummary:
    """Return high-level import and spending stats for the UI."""

    row = conn.execute(
        """
        SELECT
            COUNT(*) AS transaction_count,
            COALESCE(SUM(CASE WHEN amount < 0 AND is_excluded = 0 AND COALESCE(category, '') <> 'Transfer' THEN ABS(amount) ELSE 0 END), 0) AS spending_total,
            COALESCE(SUM(CASE WHEN amount > 0 AND is_excluded = 0 AND COALESCE(category, '') <> 'Transfer' THEN amount ELSE 0 END), 0) AS income_total
        FROM transactions
        WHERE user_id = ?
        """,
        (user_id,),
    ).fetchone()
    recent_transactions = conn.execute(
        """
        SELECT date, description, amount, category, transaction_type, source
        FROM transactions
        WHERE user_id = ?
        ORDER BY date DESC, id DESC
        LIMIT ?
        """,
        (user_id, limit),
    ).fetchall()
    spending_by_category = conn.execute(
        """
        SELECT category, ROUND(SUM(ABS(amount)), 2) AS total
        FROM transactions
        WHERE user_id = ? AND amount < 0 AND is_excluded = 0 AND COALESCE(category, '') <> 'Transfer'
        GROUP BY category
        ORDER BY total DESC, category ASC
        """,
        (user_id,),
    ).fetchall()
    account_count = conn.execute(
        "SELECT COUNT(*) FROM accounts WHERE user_id = ?",
        (user_id,),
    ).fetchone()[0]

    return ImportSummary(
        imported_count=int(row["transaction_count"] or 0),
        transaction_count=int(row["transaction_count"] or 0),
        spending_total=float(row["spending_total"] or 0),
        income_total=float(row["income_total"] or 0),
        account_count=int(account_count or 0),
        recent_transactions=recent_transactions,
        spending_by_category=spending_by_category,
    )

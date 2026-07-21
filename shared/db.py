"""SQLite connection and schema initialization."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parent.parent / "financial_gps.db"

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    email           TEXT UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,
    name            TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS accounts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    type            TEXT NOT NULL,
    balance         REAL DEFAULT 0,
    is_imported     BOOLEAN DEFAULT 0,
    account_key     TEXT,
    account_number_hint TEXT,
    last_imported_at DATETIME,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS split_groups (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    parent_txn_id   INTEGER,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cash_offsets (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    cash_txn_id     INTEGER,
    offset_txn_id   INTEGER,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transactions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id             INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    account_id          INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
    date                DATE NOT NULL,
    description         TEXT,
    amount              REAL NOT NULL,
    category            TEXT,
    transaction_type    TEXT DEFAULT 'expense',
    is_recurring        BOOLEAN DEFAULT 0,
    is_excluded         BOOLEAN DEFAULT 0,
    transfer_match_id   INTEGER REFERENCES transactions(id),
    split_group_id      INTEGER REFERENCES split_groups(id),
    cash_offset_id      INTEGER REFERENCES cash_offsets(id),
    source              TEXT DEFAULT 'csv_import',
    raw_description     TEXT,
    import_hash         TEXT,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS import_batches (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id             INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename            TEXT NOT NULL,
    format_name         TEXT NOT NULL,
    imported_count      INTEGER DEFAULT 0,
    duplicate_count     INTEGER DEFAULT 0,
    transfer_count      INTEGER DEFAULT 0,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    undone_at           DATETIME
);

CREATE TABLE IF NOT EXISTS category_rules (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    keyword         TEXT NOT NULL,
    category        TEXT NOT NULL,
    priority        INTEGER DEFAULT 0,
    source          TEXT DEFAULT 'user',
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS goals (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id             INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name                TEXT NOT NULL,
    target_amount       REAL NOT NULL,
    current_amount      REAL DEFAULT 0,
    monthly_contribution REAL DEFAULT 0,
    target_date         DATE,
    goal_type           TEXT DEFAULT 'other',
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS scenarios (
    id              TEXT PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    scenario_type   TEXT NOT NULL,
    inputs          TEXT,
    outputs         TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fire_profiles (
    id                  TEXT PRIMARY KEY,
    user_id             INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    province            TEXT,
    date_of_birth       DATE,
    is_canadian_resident BOOLEAN DEFAULT 1,
    years_in_canada_post_18 INTEGER,
    is_quebec           BOOLEAN DEFAULT 0,
    fire_variant        TEXT,
    target_retire_year  INTEGER,
    spending_floor      REAL,
    spending_ceiling    REAL,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fire_income_sources (
    id              TEXT PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    source_type     TEXT NOT NULL,
    annual_amount   REAL DEFAULT 0,
    income_character TEXT DEFAULT 'employment',
    start_year      INTEGER,
    end_year        INTEGER,
    inflation_rate  REAL DEFAULT 0.03,
    is_pensionable  BOOLEAN DEFAULT 1,
    is_override     BOOLEAN DEFAULT 0,
    csv_derived_at  DATETIME
);

CREATE TABLE IF NOT EXISTS fire_spending_baseline (
    id              TEXT PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category        TEXT NOT NULL,
    monthly_amount  REAL DEFAULT 0,
    inflation_rate  REAL DEFAULT 0.025,
    is_essential    BOOLEAN DEFAULT 1,
    is_override     BOOLEAN DEFAULT 0,
    csv_derived_at  DATETIME,
    UNIQUE(user_id, category)
);

CREATE TABLE IF NOT EXISTS fire_investment_accounts (
    id              TEXT PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    account_type    TEXT NOT NULL,
    current_balance REAL DEFAULT 0,
    opened_date     DATE,
    institution     TEXT,
    beneficiary_type TEXT
);

CREATE TABLE IF NOT EXISTS fire_account_room_history (
    id              TEXT PRIMARY KEY,
    account_id      TEXT NOT NULL REFERENCES fire_investment_accounts(id) ON DELETE CASCADE,
    event_date      DATE NOT NULL,
    event_type      TEXT NOT NULL,
    amount          REAL NOT NULL,
    room_after      REAL,
    notes           TEXT
);

CREATE TABLE IF NOT EXISTS fire_tfsa_room_state (
    user_id                 INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    snapshot_year           INTEGER,
    prior_unused_room       REAL DEFAULT 0,
    annual_limit            REAL DEFAULT 7000,
    prior_year_withdrawals  REAL DEFAULT 0,
    ytd_contributions       REAL DEFAULT 0,
    available_room          REAL DEFAULT 0,
    was_non_resident        BOOLEAN DEFAULT 0
);

CREATE TABLE IF NOT EXISTS fire_rrsp_room_state (
    user_id                     INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    snapshot_year               INTEGER,
    prior_unused_room           REAL DEFAULT 0,
    prior_year_earned_income    REAL DEFAULT 0,
    annual_rrsp_max             REAL DEFAULT 33810,
    pension_adjustment          REAL DEFAULT 0,
    par_amount                  REAL DEFAULT 0,
    pspa_amount                 REAL DEFAULT 0,
    deduction_limit             REAL DEFAULT 0,
    ytd_contributions           REAL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS fire_fhsa_state (
    user_id                     INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    account_id                  TEXT REFERENCES fire_investment_accounts(id),
    open_date                   DATE,
    is_first_time_buyer         BOOLEAN DEFAULT 1,
    annual_room                 REAL DEFAULT 8000,
    carryforward_room           REAL DEFAULT 0,
    lifetime_participation_room REAL DEFAULT 40000,
    qualifying_withdrawal_date  DATE,
    closure_status              TEXT DEFAULT 'open',
    post_closure_destination    TEXT
);

CREATE TABLE IF NOT EXISTS fire_benefit_enrollments (
    id                      TEXT PRIMARY KEY,
    user_id                 INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    benefit_type            TEXT NOT NULL,
    elected_start_age       INTEGER,
    estimated_monthly_amount REAL,
    source                  TEXT DEFAULT 'user_estimate',
    cpp_estimate_at_65      REAL,
    oas_years_resident      INTEGER,
    UNIQUE(user_id, benefit_type)
);

CREATE TABLE IF NOT EXISTS fire_projection_years (
    id                  TEXT PRIMARY KEY,
    scenario_id         TEXT NOT NULL REFERENCES scenarios(id) ON DELETE CASCADE,
    year                INTEGER NOT NULL,
    employment_income   REAL DEFAULT 0,
    cpp_received        REAL DEFAULT 0,
    oas_received        REAL DEFAULT 0,
    gis_received        REAL DEFAULT 0,
    investment_income   REAL DEFAULT 0,
    federal_tax         REAL DEFAULT 0,
    provincial_tax      REAL DEFAULT 0,
    oas_recovery_tax    REAL DEFAULT 0,
    effective_rate      REAL DEFAULT 0,
    tfsa_balance        REAL DEFAULT 0,
    rrsp_balance        REAL DEFAULT 0,
    fhsa_balance        REAL DEFAULT 0,
    taxable_balance     REAL DEFAULT 0,
    total_income        REAL DEFAULT 0,
    total_spending      REAL DEFAULT 0,
    net_surplus         REAL DEFAULT 0,
    net_worth           REAL DEFAULT 0,
    triggered_rules     TEXT,
    sequencer_notes     TEXT
);

CREATE TABLE IF NOT EXISTS forecast_assumptions (
    id                              TEXT PRIMARY KEY,
    version                         TEXT NOT NULL,
    effective_date                  DATE NOT NULL,
    mode                            TEXT DEFAULT 'expected',
    inflation_general               REAL DEFAULT 0.025,
    inflation_housing               REAL DEFAULT 0.03,
    equity_return                   REAL DEFAULT 0.07,
    bond_return                     REAL DEFAULT 0.04,
    tfsa_annual_limits              TEXT,
    rrsp_annual_max                 TEXT,
    cpp_ympe                        REAL,
    cpp2_yampe                      REAL,
    cpp_max_monthly_at_65           REAL,
    oas_max_monthly_65_74           REAL,
    oas_max_monthly_75_plus         REAL,
    oas_recovery_threshold          REAL,
    gis_earned_income_full_exempt   REAL,
    gis_earned_income_partial_exempt REAL,
    gis_single_threshold            REAL,
    gis_couple_threshold            REAL
);

CREATE INDEX IF NOT EXISTS idx_transactions_user_date ON transactions(user_id, date);
CREATE INDEX IF NOT EXISTS idx_transactions_account ON transactions(account_id);
CREATE INDEX IF NOT EXISTS idx_accounts_user ON accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_goals_user ON goals(user_id);
CREATE INDEX IF NOT EXISTS idx_scenarios_user ON scenarios(user_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_transactions_import_hash ON transactions(import_hash);
"""


def get_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else DB_PATH
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection | None = None) -> None:
    close_after = conn is None
    db = conn or get_connection()
    db.executescript(SCHEMA_SQL)
    _ensure_column(db, "accounts", "account_key", "TEXT")
    _ensure_column(db, "accounts", "account_number_hint", "TEXT")
    _ensure_column(db, "accounts", "last_imported_at", "DATETIME")
    _ensure_column(db, "transactions", "import_batch_id", "INTEGER REFERENCES import_batches(id)")
    _ensure_unique_account_key_index(db)
    _ensure_unique_import_hash_index(db)
    db.commit()
    if close_after:
        db.close()


def _table_columns(db: sqlite3.Connection, table: str) -> set[str]:
    rows = db.execute(f"PRAGMA table_info({table})").fetchall()
    return {row[1] for row in rows}


def _ensure_column(db: sqlite3.Connection, table: str, column: str, ddl: str) -> None:
    if column in _table_columns(db, table):
        return
    db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")


def _ensure_unique_account_key_index(db: sqlite3.Connection) -> None:
    db.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_accounts_user_account_key
        ON accounts(user_id, account_key)
        WHERE account_key IS NOT NULL
        """
    )


def _ensure_unique_import_hash_index(db: sqlite3.Connection) -> None:
    db.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_transactions_import_hash
        ON transactions(import_hash)
        WHERE import_hash IS NOT NULL
        """
    )


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return dict(row)

"""DB-backed FIRE planner service helpers."""

from __future__ import annotations

import sqlite3
from datetime import date
from uuid import uuid4

from fire_engine.calculators import (
    calculate_fhsa_state,
    calculate_rrsp_room,
    calculate_tfsa_room,
    estimate_cpp_monthly,
    estimate_oas_monthly,
)
from fire_engine.engine.projection import project_household
from fire_engine.models import BenefitEnrollment, Household, IncomeSource, InvestmentAccount, Person
from shared.models import DataQualityWarning
from shared.utils import utc_now_iso


def _today_year() -> int:
    return date.today().year


def get_or_create_fire_profile(conn: sqlite3.Connection, user_id: int) -> dict:
    row = conn.execute(
        "SELECT * FROM fire_profiles WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    if row:
        return dict(row)

    profile_id = str(uuid4())
    conn.execute(
        """
        INSERT INTO fire_profiles (id, user_id, created_at, updated_at)
        VALUES (?, ?, ?, ?)
        """,
        (profile_id, user_id, utc_now_iso(), utc_now_iso()),
    )
    conn.commit()
    return dict(
        conn.execute("SELECT * FROM fire_profiles WHERE user_id = ?", (user_id,)).fetchone()
    )


def save_fire_profile(conn: sqlite3.Connection, user_id: int, **fields: object) -> dict:
    profile = get_or_create_fire_profile(conn, user_id)
    allowed = {
        "province",
        "date_of_birth",
        "is_canadian_resident",
        "years_in_canada_post_18",
        "is_quebec",
        "fire_variant",
        "target_retire_year",
        "spending_floor",
        "spending_ceiling",
    }
    updates = {key: value for key, value in fields.items() if key in allowed}
    if not updates:
        return profile

    updates["updated_at"] = utc_now_iso()
    assignments = ", ".join(f"{key} = ?" for key in updates)
    values = [value.isoformat() if isinstance(value, date) else value for value in updates.values()]
    conn.execute(
        f"UPDATE fire_profiles SET {assignments} WHERE user_id = ?",
        (*values, user_id),
    )
    conn.commit()
    return dict(conn.execute("SELECT * FROM fire_profiles WHERE user_id = ?", (user_id,)).fetchone())


def list_fire_income_sources(conn: sqlite3.Connection, user_id: int) -> list[dict]:
    rows = conn.execute(
        """
        SELECT *
        FROM fire_income_sources
        WHERE user_id = ?
        ORDER BY source_type, start_year, id
        """,
        (user_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def upsert_fire_income_source(
    conn: sqlite3.Connection,
    user_id: int,
    source_type: str,
    annual_amount: float,
    *,
    income_character: str = "employment",
    start_year: int | None = None,
    end_year: int | None = None,
    inflation_rate: float = 0.03,
    is_pensionable: bool = True,
    is_override: bool = True,
) -> None:
    row = conn.execute(
        """
        SELECT id
        FROM fire_income_sources
        WHERE user_id = ? AND source_type = ?
        ORDER BY id ASC
        LIMIT 1
        """,
        (user_id, source_type),
    ).fetchone()
    if row:
        conn.execute(
            """
            UPDATE fire_income_sources
            SET annual_amount = ?, income_character = ?, start_year = ?, end_year = ?,
                inflation_rate = ?, is_pensionable = ?, is_override = ?
            WHERE id = ?
            """,
            (annual_amount, income_character, start_year, end_year, inflation_rate, int(is_pensionable), int(is_override), row["id"]),
        )
    else:
        conn.execute(
            """
            INSERT INTO fire_income_sources (
                id, user_id, source_type, annual_amount, income_character,
                start_year, end_year, inflation_rate, is_pensionable, is_override
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid4()),
                user_id,
                source_type,
                annual_amount,
                income_character,
                start_year,
                end_year,
                inflation_rate,
                int(is_pensionable),
                int(is_override),
            ),
        )
    conn.commit()


def list_fire_spending_baseline(conn: sqlite3.Connection, user_id: int) -> list[dict]:
    rows = conn.execute(
        """
        SELECT *
        FROM fire_spending_baseline
        WHERE user_id = ?
        ORDER BY category ASC
        """,
        (user_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def upsert_fire_spending_category(
    conn: sqlite3.Connection,
    user_id: int,
    category: str,
    monthly_amount: float,
    *,
    inflation_rate: float = 0.025,
    is_essential: bool = True,
    is_override: bool = True,
) -> None:
    row = conn.execute(
        """
        SELECT id
        FROM fire_spending_baseline
        WHERE user_id = ? AND category = ?
        """,
        (user_id, category),
    ).fetchone()
    if row:
        conn.execute(
            """
            UPDATE fire_spending_baseline
            SET monthly_amount = ?, inflation_rate = ?, is_essential = ?, is_override = ?
            WHERE id = ?
            """,
            (monthly_amount, inflation_rate, int(is_essential), int(is_override), row["id"]),
        )
    else:
        conn.execute(
            """
            INSERT INTO fire_spending_baseline (
                id, user_id, category, monthly_amount, inflation_rate, is_essential, is_override
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (str(uuid4()), user_id, category, monthly_amount, inflation_rate, int(is_essential), int(is_override)),
        )
    conn.commit()


def list_investment_accounts(conn: sqlite3.Connection, user_id: int) -> list[dict]:
    rows = conn.execute(
        """
        SELECT *
        FROM fire_investment_accounts
        WHERE user_id = ?
        ORDER BY account_type, id
        """,
        (user_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def upsert_investment_account(
    conn: sqlite3.Connection,
    user_id: int,
    account_type: str,
    current_balance: float,
    *,
    opened_date: date | None = None,
    institution: str | None = None,
) -> None:
    row = conn.execute(
        """
        SELECT id
        FROM fire_investment_accounts
        WHERE user_id = ? AND account_type = ?
        ORDER BY id ASC
        LIMIT 1
        """,
        (user_id, account_type),
    ).fetchone()
    if row:
        conn.execute(
            """
            UPDATE fire_investment_accounts
            SET current_balance = ?, opened_date = ?, institution = ?
            WHERE id = ?
            """,
            (current_balance, opened_date.isoformat() if isinstance(opened_date, date) else opened_date, institution, row["id"]),
        )
    else:
        conn.execute(
            """
            INSERT INTO fire_investment_accounts (id, user_id, account_type, current_balance, opened_date, institution)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (str(uuid4()), user_id, account_type, current_balance, opened_date.isoformat() if isinstance(opened_date, date) else opened_date, institution),
        )
    conn.commit()


def get_or_create_tfsa_state(conn: sqlite3.Connection, user_id: int) -> dict:
    row = conn.execute("SELECT * FROM fire_tfsa_room_state WHERE user_id = ?", (user_id,)).fetchone()
    if row:
        return dict(row)
    conn.execute(
        """
        INSERT INTO fire_tfsa_room_state (user_id, snapshot_year)
        VALUES (?, ?)
        """,
        (user_id, _today_year()),
    )
    conn.commit()
    return dict(conn.execute("SELECT * FROM fire_tfsa_room_state WHERE user_id = ?", (user_id,)).fetchone())


def save_tfsa_state(conn: sqlite3.Connection, user_id: int, **fields: object) -> dict:
    get_or_create_tfsa_state(conn, user_id)
    allowed = {
        "snapshot_year",
        "prior_unused_room",
        "annual_limit",
        "prior_year_withdrawals",
        "ytd_contributions",
        "available_room",
        "was_non_resident",
    }
    updates = {key: value for key, value in fields.items() if key in allowed}
    if updates:
        assignments = ", ".join(f"{key} = ?" for key in updates)
        conn.execute(
            f"UPDATE fire_tfsa_room_state SET {assignments} WHERE user_id = ?",
            (*updates.values(), user_id),
        )
        conn.commit()
    return dict(conn.execute("SELECT * FROM fire_tfsa_room_state WHERE user_id = ?", (user_id,)).fetchone())


def get_or_create_rrsp_state(conn: sqlite3.Connection, user_id: int) -> dict:
    row = conn.execute("SELECT * FROM fire_rrsp_room_state WHERE user_id = ?", (user_id,)).fetchone()
    if row:
        return dict(row)
    conn.execute(
        """
        INSERT INTO fire_rrsp_room_state (user_id, snapshot_year)
        VALUES (?, ?)
        """,
        (user_id, _today_year()),
    )
    conn.commit()
    return dict(conn.execute("SELECT * FROM fire_rrsp_room_state WHERE user_id = ?", (user_id,)).fetchone())


def save_rrsp_state(conn: sqlite3.Connection, user_id: int, **fields: object) -> dict:
    get_or_create_rrsp_state(conn, user_id)
    allowed = {
        "snapshot_year",
        "prior_unused_room",
        "prior_year_earned_income",
        "annual_rrsp_max",
        "pension_adjustment",
        "par_amount",
        "pspa_amount",
        "deduction_limit",
        "ytd_contributions",
    }
    updates = {key: value for key, value in fields.items() if key in allowed}
    if updates:
        assignments = ", ".join(f"{key} = ?" for key in updates)
        conn.execute(
            f"UPDATE fire_rrsp_room_state SET {assignments} WHERE user_id = ?",
            (*updates.values(), user_id),
        )
        conn.commit()
    return dict(conn.execute("SELECT * FROM fire_rrsp_room_state WHERE user_id = ?", (user_id,)).fetchone())


def get_or_create_fhsa_state(conn: sqlite3.Connection, user_id: int) -> dict:
    row = conn.execute("SELECT * FROM fire_fhsa_state WHERE user_id = ?", (user_id,)).fetchone()
    if row:
        return dict(row)
    conn.execute(
        """
        INSERT INTO fire_fhsa_state (user_id, annual_room, carryforward_room, lifetime_participation_room)
        VALUES (?, 8000, 0, 40000)
        """,
        (user_id,),
    )
    conn.commit()
    return dict(conn.execute("SELECT * FROM fire_fhsa_state WHERE user_id = ?", (user_id,)).fetchone())


def save_fhsa_state(conn: sqlite3.Connection, user_id: int, **fields: object) -> dict:
    get_or_create_fhsa_state(conn, user_id)
    allowed = {
        "account_id",
        "open_date",
        "is_first_time_buyer",
        "annual_room",
        "carryforward_room",
        "lifetime_participation_room",
        "qualifying_withdrawal_date",
        "closure_status",
        "post_closure_destination",
    }
    updates = {key: value for key, value in fields.items() if key in allowed}
    if updates:
        assignments = ", ".join(f"{key} = ?" for key in updates)
        values = [value.isoformat() if isinstance(value, date) else value for value in updates.values()]
        conn.execute(
            f"UPDATE fire_fhsa_state SET {assignments} WHERE user_id = ?",
            (*values, user_id),
        )
        conn.commit()
    return dict(conn.execute("SELECT * FROM fire_fhsa_state WHERE user_id = ?", (user_id,)).fetchone())


def list_benefit_enrollments(conn: sqlite3.Connection, user_id: int) -> list[dict]:
    rows = conn.execute(
        """
        SELECT *
        FROM fire_benefit_enrollments
        WHERE user_id = ?
        ORDER BY benefit_type
        """,
        (user_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def upsert_benefit_enrollment(
    conn: sqlite3.Connection,
    user_id: int,
    benefit_type: str,
    elected_start_age: int,
    *,
    estimated_monthly_amount: float | None = None,
    source: str = "calculated",
    cpp_estimate_at_65: float | None = None,
    oas_years_resident: int | None = None,
) -> None:
    row = conn.execute(
        """
        SELECT id
        FROM fire_benefit_enrollments
        WHERE user_id = ? AND benefit_type = ?
        """,
        (user_id, benefit_type),
    ).fetchone()
    if row:
        conn.execute(
            """
            UPDATE fire_benefit_enrollments
            SET elected_start_age = ?, estimated_monthly_amount = ?, source = ?,
                cpp_estimate_at_65 = ?, oas_years_resident = ?
            WHERE id = ?
            """,
            (elected_start_age, estimated_monthly_amount, source, cpp_estimate_at_65, oas_years_resident, row["id"]),
        )
    else:
        conn.execute(
            """
            INSERT INTO fire_benefit_enrollments (
                id, user_id, benefit_type, elected_start_age, estimated_monthly_amount,
                source, cpp_estimate_at_65, oas_years_resident
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (str(uuid4()), user_id, benefit_type, elected_start_age, estimated_monthly_amount, source, cpp_estimate_at_65, oas_years_resident),
        )
    conn.commit()


def _parse_date(value: object) -> date | None:
    if not value:
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def build_household(conn: sqlite3.Connection, user_id: int) -> Household | None:
    profile = get_or_create_fire_profile(conn, user_id)
    dob = _parse_date(profile.get("date_of_birth"))
    if dob is None or not profile.get("province"):
        return None

    person = Person(
        name="User",
        date_of_birth=dob,
        province=profile.get("province") or "ON",
        years_in_canada_post_18=int(profile.get("years_in_canada_post_18") or 40),
        is_canadian_resident=bool(profile.get("is_canadian_resident", 1)),
        is_quebec=bool(profile.get("is_quebec", 0)),
    )
    income_sources = [
        IncomeSource(
            source_type=row["source_type"],
            annual_amount=float(row["annual_amount"] or 0),
            income_character=row.get("income_character") or "employment",
            start_year=row.get("start_year"),
            end_year=row.get("end_year"),
            inflation_rate=float(row.get("inflation_rate") or 0.03),
            is_pensionable=bool(row.get("is_pensionable", 1)),
        )
        for row in list_fire_income_sources(conn, user_id)
    ]
    accounts = [
        InvestmentAccount(
            account_type=row["account_type"],
            current_balance=float(row["current_balance"] or 0),
            opened_date=_parse_date(row.get("opened_date")),
            institution=row.get("institution"),
        )
        for row in list_investment_accounts(conn, user_id)
    ]
    benefits = [
        BenefitEnrollment(
            benefit_type=row["benefit_type"],
            elected_start_age=int(row["elected_start_age"] or 65),
            estimated_monthly_amount=float(row["estimated_monthly_amount"]) if row.get("estimated_monthly_amount") is not None else None,
            source=row.get("source") or "calculated",
            cpp_estimate_at_65=float(row["cpp_estimate_at_65"]) if row.get("cpp_estimate_at_65") is not None else None,
            oas_years_resident=int(row["oas_years_resident"] or person.years_in_canada_post_18),
        )
        for row in list_benefit_enrollments(conn, user_id)
    ]
    baseline = list_fire_spending_baseline(conn, user_id)
    annual_spending = sum(float(row["monthly_amount"] or 0) for row in baseline) * 12 if baseline else 60000
    return Household(
        primary=person,
        income_sources=income_sources,
        accounts=accounts,
        benefits=benefits,
        annual_spending=annual_spending,
        spending_inflation=0.025,
        start_year=_today_year(),
    )


def calculate_room_snapshots(conn: sqlite3.Connection, user_id: int) -> dict[str, object]:
    tfsa = get_or_create_tfsa_state(conn, user_id)
    rrsp = get_or_create_rrsp_state(conn, user_id)
    fhsa = get_or_create_fhsa_state(conn, user_id)
    return {
        "tfsa": calculate_tfsa_room(
            snapshot_year=int(tfsa.get("snapshot_year") or _today_year()),
            prior_unused_room=float(tfsa.get("prior_unused_room") or 0),
            prior_year_withdrawals=float(tfsa.get("prior_year_withdrawals") or 0),
            ytd_contributions=float(tfsa.get("ytd_contributions") or 0),
            was_non_resident=bool(tfsa.get("was_non_resident", 0)),
        ),
        "rrsp": calculate_rrsp_room(
            snapshot_year=int(rrsp.get("snapshot_year") or _today_year()),
            prior_unused_room=float(rrsp.get("prior_unused_room") or 0),
            prior_year_earned_income=float(rrsp.get("prior_year_earned_income") or 0),
            pension_adjustment=float(rrsp.get("pension_adjustment") or 0),
            par_amount=float(rrsp.get("par_amount") or 0),
            pspa_amount=float(rrsp.get("pspa_amount") or 0),
            ytd_contributions=float(rrsp.get("ytd_contributions") or 0),
        ),
        "fhsa": calculate_fhsa_state(
            snapshot_year=_today_year(),
            open_date=_parse_date(fhsa.get("open_date")),
            carryforward_room=float(fhsa.get("carryforward_room") or 0),
            lifetime_contributions=float(
                max(float(fhsa.get("lifetime_participation_room") or 40000) - 40000, 0)
            ),
            is_first_time_buyer=bool(fhsa.get("is_first_time_buyer", 1)),
        ),
    }


def project_user_household(conn: sqlite3.Connection, user_id: int, years: int = 40) -> list[object]:
    household = build_household(conn, user_id)
    if household is None:
        return []
    return project_household(household, years=years)


def estimate_fire_date(conn: sqlite3.Connection, user_id: int) -> int | None:
    profile = get_or_create_fire_profile(conn, user_id)
    annual_spending = float(profile.get("spending_floor") or 0)
    if annual_spending <= 0:
        baseline = list_fire_spending_baseline(conn, user_id)
        annual_spending = sum(float(row["monthly_amount"] or 0) for row in baseline) * 12
    if annual_spending <= 0:
        return None

    target = annual_spending * 25
    projection = project_user_household(conn, user_id, years=40)
    for year in projection:
        if float(year.net_worth) >= target:
            return int(year.year)
    return None


def get_data_quality_warnings(conn: sqlite3.Connection, user_id: int) -> list[DataQualityWarning]:
    warnings: list[DataQualityWarning] = []
    profile = get_or_create_fire_profile(conn, user_id)
    tfsa = get_or_create_tfsa_state(conn, user_id)
    get_or_create_rrsp_state(conn, user_id)
    fhsa = get_or_create_fhsa_state(conn, user_id)
    benefits = {row["benefit_type"]: row for row in list_benefit_enrollments(conn, user_id)}
    accounts = list_investment_accounts(conn, user_id)

    warnings.append(
        DataQualityWarning(
            "tax_parameter_fallback",
            "Forecast years without verified CRA parameters use flat 2026 tax and benefit values.",
            "info",
        )
    )

    txn_count = conn.execute("SELECT COUNT(*) FROM transactions WHERE user_id = ?", (user_id,)).fetchone()[0]
    if txn_count == 0:
        warnings.append(DataQualityWarning("no_csv", "No CSV imported - FIRE defaults are not transaction-backed.", "warning"))
    if not profile.get("province"):
        warnings.append(DataQualityWarning("province_missing", "Province not set.", "error"))
    if not profile.get("date_of_birth"):
        warnings.append(DataQualityWarning("dob_missing", "Date of birth missing.", "error"))
    if not tfsa.get("snapshot_year") or float(tfsa.get("available_room") or 0) == 0:
        warnings.append(DataQualityWarning("tfsa_unverified", "TFSA room unverified.", "warning"))
    cpp = benefits.get("CPP")
    if not cpp or cpp.get("estimated_monthly_amount") is None:
        warnings.append(DataQualityWarning("cpp_missing", "CPP estimate missing.", "warning"))
    if any((acct.get("account_type") or "").lower() == "taxable" for acct in accounts):
        warnings.append(DataQualityWarning("acb_unknown", "ACB unknown for taxable accounts.", "warning"))
    if profile.get("date_of_birth"):
        dob = _parse_date(profile.get("date_of_birth"))
        if dob is not None:
            turns_71 = dob.year + 71
            if turns_71 - _today_year() <= 2:
                warnings.append(DataQualityWarning("rrsp_age_71", "RRSP age-71 approaching.", "warning"))
    if fhsa.get("open_date"):
        fhsa_snapshot = calculate_fhsa_state(
            snapshot_year=_today_year(),
            open_date=_parse_date(fhsa.get("open_date")),
            carryforward_room=float(fhsa.get("carryforward_room") or 0),
            is_first_time_buyer=bool(fhsa.get("is_first_time_buyer", 1)),
        )
        if fhsa_snapshot.years_until_expiry is not None and fhsa_snapshot.years_until_expiry < 2:
            warnings.append(DataQualityWarning("fhsa_expiry", "FHSA expiry warning.", "warning"))
    income_sources = list_fire_income_sources(conn, user_id)
    if any(abs(float(row["annual_amount"] or 0) - 95323) <= 15000 for row in income_sources):
        warnings.append(DataQualityWarning("oas_threshold", "Projected income is close to the OAS recovery threshold.", "warning"))
    return warnings


def benefit_previews(conn: sqlite3.Connection, user_id: int) -> dict[str, object]:
    profile = get_or_create_fire_profile(conn, user_id)
    dob = _parse_date(profile.get("date_of_birth")) or date(_today_year() - 40, 1, 1)
    age = _today_year() - dob.year
    years_resident = int(profile.get("years_in_canada_post_18") or 40)
    cpp65 = estimate_cpp_monthly(0.7, 65)
    return {
        "cpp_60": estimate_cpp_monthly(0.7, 60),
        "cpp_65": cpp65,
        "cpp_70": estimate_cpp_monthly(0.7, 70),
        "oas_65": estimate_oas_monthly(max(age, 65), 65, years_resident),
        "oas_70": estimate_oas_monthly(max(age, 70), 70, years_resident),
    }

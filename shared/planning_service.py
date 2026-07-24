"""Versioned, user-isolated planning records and projection adapters."""

from __future__ import annotations

from copy import deepcopy
from datetime import date
import json
import sqlite3
from uuid import uuid4

from fire_engine.engine.projection import project_household
from fire_engine.models import BenefitEnrollment, Household, IncomeSource, InvestmentAccount, Person
from shared.fire_service import (
    get_or_create_fhsa_state,
    get_or_create_fire_profile,
    get_or_create_rrsp_state,
    get_or_create_tfsa_state,
    list_benefit_enrollments,
    list_fire_income_sources,
    list_fire_spending_baseline,
    list_investment_accounts,
)
from shared.utils import utc_now_iso


PLAN_PAYLOAD_VERSION = 1
REFRESHABLE_SECTIONS = {"profile", "income", "spending", "accounts", "benefits", "room"}


def blank_plan_payload() -> dict:
    return {
        "version": PLAN_PAYLOAD_VERSION,
        "profile": {
            "province": None,
            "date_of_birth": None,
            "is_canadian_resident": True,
            "years_in_canada_post_18": 40,
            "is_quebec": False,
            "fire_variant": "regular",
            "target_retire_year": date.today().year + 15,
            "spending_floor": 50000.0,
            "spending_ceiling": 65000.0,
        },
        "income": [],
        "spending": [],
        "accounts": [],
        "benefits": [],
        "room": {"tfsa": {}, "rrsp": {}, "fhsa": {}},
        "assumptions": {
            "start_year": date.today().year,
            "projection_years": 40,
            "spending_inflation": 0.025,
        },
        "provenance": {"source": "manual", "refreshed_at": None, "sections": {}},
    }


def snapshot_current_finances(conn: sqlite3.Connection, user_id: int) -> dict:
    payload = blank_plan_payload()
    profile = get_or_create_fire_profile(conn, user_id)
    payload["profile"].update(
        {
            key: profile.get(key)
            for key in payload["profile"]
            if key in profile
        }
    )
    payload["income"] = list_fire_income_sources(conn, user_id)
    payload["spending"] = list_fire_spending_baseline(conn, user_id)
    payload["accounts"] = list_investment_accounts(conn, user_id)
    payload["benefits"] = list_benefit_enrollments(conn, user_id)
    payload["room"] = {
        "tfsa": get_or_create_tfsa_state(conn, user_id),
        "rrsp": get_or_create_rrsp_state(conn, user_id),
        "fhsa": get_or_create_fhsa_state(conn, user_id),
    }
    refreshed_at = utc_now_iso()
    payload["provenance"] = {
        "source": "current_finances",
        "refreshed_at": refreshed_at,
        "sections": {section: refreshed_at for section in REFRESHABLE_SECTIONS},
    }
    return payload


def validate_plan_payload(payload: dict) -> dict:
    candidate = deepcopy(payload)
    if candidate.get("version") != PLAN_PAYLOAD_VERSION:
        raise ValueError(f"Unsupported plan payload version: {candidate.get('version')}")
    required = {"profile", "income", "spending", "accounts", "benefits", "room", "assumptions", "provenance"}
    missing = required - candidate.keys()
    if missing:
        raise ValueError(f"Plan payload is missing: {', '.join(sorted(missing))}")
    assumptions = candidate["assumptions"]
    years = int(assumptions.get("projection_years", 40))
    if years < 1 or years > 100:
        raise ValueError("Projection years must be between 1 and 100.")
    assumptions["projection_years"] = years
    assumptions["spending_inflation"] = float(assumptions.get("spending_inflation", 0.025))
    return candidate


def _next_revision(conn: sqlite3.Connection, plan_id: str) -> int:
    row = conn.execute(
        "SELECT COALESCE(MAX(revision_number), 0) + 1 FROM planning_plan_revisions WHERE plan_id = ?",
        (plan_id,),
    ).fetchone()
    return int(row[0])


def save_plan_revision(
    conn: sqlite3.Connection,
    user_id: int,
    plan_id: str,
    payload: dict,
    *,
    reason: str = "edit",
) -> dict:
    owned = conn.execute(
        "SELECT id FROM planning_plans WHERE id = ? AND user_id = ? AND status = 'active'",
        (plan_id, user_id),
    ).fetchone()
    if not owned:
        raise ValueError("Plan not found.")
    validated = validate_plan_payload(payload)
    revision_id = str(uuid4())
    revision_number = _next_revision(conn, plan_id)
    now = utc_now_iso()
    conn.execute(
        """
        INSERT INTO planning_plan_revisions
            (id, plan_id, revision_number, payload, reason, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (revision_id, plan_id, revision_number, json.dumps(validated, sort_keys=True), reason, now),
    )
    conn.execute("UPDATE planning_plans SET updated_at = ? WHERE id = ?", (now, plan_id))
    conn.commit()
    return {"id": revision_id, "revision_number": revision_number, "payload": validated, "reason": reason}


def create_plan(
    conn: sqlite3.Connection,
    user_id: int,
    name: str,
    *,
    from_current_finances: bool = True,
) -> dict:
    plan_id = str(uuid4())
    now = utc_now_iso()
    has_active = conn.execute(
        "SELECT 1 FROM planning_plans WHERE user_id = ? AND is_active = 1 AND status = 'active'",
        (user_id,),
    ).fetchone()
    conn.execute(
        """
        INSERT INTO planning_plans (id, user_id, name, status, is_active, created_at, updated_at)
        VALUES (?, ?, ?, 'active', ?, ?, ?)
        """,
        (plan_id, user_id, name.strip() or "My Plan", 0 if has_active else 1, now, now),
    )
    payload = snapshot_current_finances(conn, user_id) if from_current_finances else blank_plan_payload()
    save_plan_revision(conn, user_id, plan_id, payload, reason="created")
    return get_plan(conn, user_id, plan_id)


def list_plans(conn: sqlite3.Connection, user_id: int, *, include_archived: bool = False) -> list[dict]:
    status_clause = "" if include_archived else "AND p.status = 'active'"
    rows = conn.execute(
        f"""
        SELECT p.*, r.revision_number, r.payload, r.reason AS revision_reason
        FROM planning_plans p
        JOIN planning_plan_revisions r ON r.plan_id = p.id
        WHERE p.user_id = ? {status_clause}
          AND r.revision_number = (
              SELECT MAX(latest.revision_number)
              FROM planning_plan_revisions latest
              WHERE latest.plan_id = p.id
          )
        ORDER BY p.is_active DESC, p.updated_at DESC
        """,
        (user_id,),
    ).fetchall()
    return [{**dict(row), "payload": json.loads(row["payload"])} for row in rows]


def get_plan(conn: sqlite3.Connection, user_id: int, plan_id: str) -> dict:
    plan = next((row for row in list_plans(conn, user_id, include_archived=True) if row["id"] == plan_id), None)
    if plan is None:
        raise ValueError("Plan not found.")
    return plan


def set_active_plan(conn: sqlite3.Connection, user_id: int, plan_id: str) -> None:
    if not conn.execute(
        "SELECT 1 FROM planning_plans WHERE id = ? AND user_id = ? AND status = 'active'",
        (plan_id, user_id),
    ).fetchone():
        raise ValueError("Plan not found.")
    conn.execute("UPDATE planning_plans SET is_active = 0 WHERE user_id = ?", (user_id,))
    conn.execute("UPDATE planning_plans SET is_active = 1 WHERE id = ? AND user_id = ?", (plan_id, user_id))
    conn.commit()


def rename_plan(conn: sqlite3.Connection, user_id: int, plan_id: str, name: str) -> None:
    cleaned = name.strip()
    if not cleaned:
        raise ValueError("Plan name is required.")
    cursor = conn.execute(
        """
        UPDATE planning_plans
        SET name = ?, updated_at = ?
        WHERE id = ? AND user_id = ? AND status = 'active'
        """,
        (cleaned, utc_now_iso(), plan_id, user_id),
    )
    if cursor.rowcount == 0:
        raise ValueError("Plan not found.")
    conn.commit()


def duplicate_plan(conn: sqlite3.Connection, user_id: int, plan_id: str, name: str | None = None) -> dict:
    source = get_plan(conn, user_id, plan_id)
    duplicate = create_plan(conn, user_id, name or f"{source['name']} copy", from_current_finances=False)
    save_plan_revision(conn, user_id, duplicate["id"], source["payload"], reason="duplicated")
    return get_plan(conn, user_id, duplicate["id"])


def archive_plan(conn: sqlite3.Connection, user_id: int, plan_id: str) -> None:
    plan = get_plan(conn, user_id, plan_id)
    conn.execute(
        "UPDATE planning_plans SET status = 'archived', is_active = 0, updated_at = ? WHERE id = ? AND user_id = ?",
        (utc_now_iso(), plan_id, user_id),
    )
    if plan["is_active"]:
        replacement = conn.execute(
            "SELECT id FROM planning_plans WHERE user_id = ? AND status = 'active' ORDER BY updated_at DESC LIMIT 1",
            (user_id,),
        ).fetchone()
        if replacement:
            conn.execute("UPDATE planning_plans SET is_active = 1 WHERE id = ?", (replacement["id"],))
    conn.commit()


def refresh_plan_sections(
    conn: sqlite3.Connection,
    user_id: int,
    plan_id: str,
    sections: set[str],
) -> dict:
    invalid = sections - REFRESHABLE_SECTIONS
    if invalid:
        raise ValueError(f"Unknown refresh sections: {', '.join(sorted(invalid))}")
    plan = get_plan(conn, user_id, plan_id)
    refreshed = snapshot_current_finances(conn, user_id)
    payload = deepcopy(plan["payload"])
    now = utc_now_iso()
    for section in sections:
        payload[section] = refreshed[section]
        payload["provenance"]["sections"][section] = now
    payload["provenance"]["refreshed_at"] = now
    return save_plan_revision(conn, user_id, plan_id, payload, reason="refresh")


def plan_payload_to_household(payload: dict) -> Household | None:
    payload = validate_plan_payload(payload)
    profile = payload["profile"]
    if not profile.get("date_of_birth") or not profile.get("province"):
        return None
    person = Person(
        name="User",
        date_of_birth=date.fromisoformat(profile["date_of_birth"]),
        province=profile["province"],
        years_in_canada_post_18=int(profile.get("years_in_canada_post_18") or 40),
        is_canadian_resident=bool(profile.get("is_canadian_resident", True)),
        is_quebec=bool(profile.get("is_quebec", False)),
    )
    income = [
        IncomeSource(
            source_type=row["source_type"],
            annual_amount=float(row.get("annual_amount") or 0),
            income_character=row.get("income_character") or "employment",
            start_year=row.get("start_year"),
            end_year=row.get("end_year"),
            inflation_rate=float(row.get("inflation_rate") or 0.03),
            is_pensionable=bool(row.get("is_pensionable", True)),
        )
        for row in payload["income"]
    ]
    accounts = [
        InvestmentAccount(
            account_type=row["account_type"],
            current_balance=float(row.get("current_balance") or 0),
            opened_date=date.fromisoformat(row["opened_date"]) if row.get("opened_date") else None,
            institution=row.get("institution"),
            beneficiary_type=row.get("beneficiary_type"),
        )
        for row in payload["accounts"]
    ]
    benefits = [
        BenefitEnrollment(
            benefit_type=row["benefit_type"],
            elected_start_age=int(row.get("elected_start_age") or 65),
            estimated_monthly_amount=(
                float(row["estimated_monthly_amount"])
                if row.get("estimated_monthly_amount") is not None
                else None
            ),
            source=row.get("source") or "calculated",
            cpp_estimate_at_65=(
                float(row["cpp_estimate_at_65"])
                if row.get("cpp_estimate_at_65") is not None
                else None
            ),
            oas_years_resident=int(row.get("oas_years_resident") or 40),
        )
        for row in payload["benefits"]
    ]
    annual_spending = sum(float(row.get("monthly_amount") or 0) for row in payload["spending"]) * 12
    assumptions = payload["assumptions"]
    return Household(
        primary=person,
        income_sources=income,
        accounts=accounts,
        benefits=benefits,
        annual_spending=annual_spending,
        spending_inflation=float(assumptions["spending_inflation"]),
        start_year=int(assumptions.get("start_year") or date.today().year),
    )


def project_plan(payload: dict) -> list:
    household = plan_payload_to_household(payload)
    if household is None:
        return []
    return project_household(household, years=int(payload["assumptions"]["projection_years"]))

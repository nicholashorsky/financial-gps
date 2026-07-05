"""Quick smoke test for the foundation and first import phase."""

from __future__ import annotations

import tempfile
import sys
import json
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import shared.db as db_module
from auth import authenticate_user, create_user
from auth import update_user_profile
from bridge.bridge_status import get_bridge_status
from bridge.data_bridge import sync_fire_defaults
from budget.categorizer import add_user_rule, list_category_rules
from budget.importer import get_spending_summary, import_csv_transactions
from budget.offset_engine import create_offset_pair
from budget.scenario_engine import run_scenario
from budget.split_engine import SplitLine, split_transaction
from fire_engine.parameters.loader import get_params
from shared.db import get_connection, init_db
from shared.fire_service import (
    estimate_fire_date,
    get_data_quality_warnings,
    project_user_household,
    save_fire_profile,
    upsert_benefit_enrollment,
    upsert_investment_account,
)
from shared.onboarding_service import get_onboarding_status


def main() -> None:
    temp_db = tempfile.NamedTemporaryFile(delete=False)
    temp_db.close()
    original_db_path = db_module.DB_PATH
    db_module.DB_PATH = Path(temp_db.name)

    try:
        init_db()
        conn = get_connection()
        try:
            tables = [
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                ).fetchall()
            ]
            print(f"{len(tables)} tables created")
            assert len(tables) >= 18, f"Expected 18+ tables, got {len(tables)}"

            params = get_params(2026, "ON")
            assert params.tfsa_annual_limit == 7000
            assert params.rrsp_max == 33810
            print("CRA params OK")

            user = create_user("smoke@test.com", "password123", "Smoke Test")
            assert user is not None
            auth = authenticate_user("smoke@test.com", "password123")
            assert auth is not None
            assert authenticate_user("smoke@test.com", "wrong") is None
            renamed = update_user_profile(int(user["id"]), name="Renamed Smoke")
            assert renamed is not None
            assert renamed["name"] == "Renamed Smoke"
            print("Auth OK")

            csv = "date,description,amount\n2026-06-01,Tim Hortons,-12.50\n2026-06-02,Payroll,3000\n"
            result, _ = import_csv_transactions(conn, int(user["id"]), csv)
            assert result.imported == 2
            summary = get_spending_summary(conn, int(user["id"]))
            assert summary.transaction_count == 2
            assert round(summary.spending_total, 2) == 12.50
            assert round(summary.income_total, 2) == 3000.00
            print("Import OK")

            add_user_rule(conn, int(user["id"]), "coffeeshop", "Dining", 80)
            rules = list_category_rules(conn, int(user["id"]))
            assert any(rule[1] == "coffeeshop" for rule in rules)
            print("Rules OK")

            account_id = conn.execute(
                "SELECT id FROM accounts WHERE user_id = ? ORDER BY id ASC LIMIT 1",
                (int(user["id"]),),
            ).fetchone()["id"]
            parent = conn.execute(
                """
                INSERT INTO transactions (user_id, account_id, date, description, amount, category, transaction_type, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'manual')
                """,
                (int(user["id"]), account_id, "2026-06-03", "Split Dinner", -12.5, "Dining", "expense"),
            )
            parent_txn_id = parent.lastrowid
            split_group_id = split_transaction(
                conn,
                int(user["id"]),
                parent_txn_id,
                [SplitLine(amount=-7.5, category="Dining"), SplitLine(amount=-5.0, category="Dining")],
            )
            split_children = conn.execute(
                "SELECT COUNT(*) FROM transactions WHERE split_group_id = ? AND id != ?",
                (split_group_id, parent_txn_id),
            ).fetchone()[0]
            assert split_children == 2
            print("Split OK")

            a = conn.execute(
                """
                INSERT INTO transactions (user_id, account_id, date, description, amount, category, transaction_type, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'manual')
                """,
                (int(user["id"]), account_id, "2026-06-04", "Cash withdrawal", -20.0, "Transfer", "transfer_out"),
            )
            b = conn.execute(
                """
                INSERT INTO transactions (user_id, account_id, date, description, amount, category, transaction_type, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'manual')
                """,
                (int(user["id"]), account_id, "2026-06-04", "Cash spend", -20.0, "Dining", "expense"),
            )
            conn.commit()
            offset_id = create_offset_pair(conn, int(user["id"]), a.lastrowid, b.lastrowid)
            offset_rows = conn.execute(
                "SELECT COUNT(*) FROM cash_offsets WHERE id = ?",
                (offset_id,),
            ).fetchone()[0]
            assert offset_rows == 1
            print("Offset OK")

            bridge_result = sync_fire_defaults(conn, int(user["id"]))
            assert bridge_result.income_synced is True
            status = get_bridge_status(conn, int(user["id"]))
            assert status["income_rows"] >= 1
            print("Bridge OK")

            scenario_result = run_scenario(
                "new_job",
                {
                    "current_salary": 80000,
                    "new_salary": 95000,
                    "commute_cost_change": 100,
                    "benefits_value_change": 1200,
                    "remote_work_savings": 50,
                    "tax_rate": 0.30,
                },
            )
            assert scenario_result.monthly_cash_flow_delta > 0
            scenario_id = str(uuid4())
            conn.execute(
                """
                INSERT INTO scenarios (id, user_id, name, scenario_type, inputs, outputs)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    scenario_id,
                    int(user["id"]),
                    "Smoke new job",
                    "new_job",
                    json.dumps({"current_salary": 80000, "new_salary": 95000}),
                    json.dumps(scenario_result.to_dict()),
                ),
            )
            conn.commit()
            saved_scenarios = conn.execute(
                "SELECT COUNT(*) FROM scenarios WHERE user_id = ?",
                (int(user["id"]),),
            ).fetchone()[0]
            assert saved_scenarios == 1
            print("Scenario OK")

            save_fire_profile(
                conn,
                int(user["id"]),
                province="ON",
                date_of_birth="1988-01-01",
                years_in_canada_post_18=40,
                fire_variant="coast",
                target_retire_year=2045,
                spending_floor=45000,
                spending_ceiling=65000,
            )
            upsert_investment_account(conn, int(user["id"]), "TFSA", 25000)
            upsert_benefit_enrollment(conn, int(user["id"]), "CPP", 65, estimated_monthly_amount=900, source="calculated")
            upsert_benefit_enrollment(conn, int(user["id"]), "OAS", 65, estimated_monthly_amount=700, source="calculated")
            projection = project_user_household(conn, int(user["id"]), years=3)
            assert len(projection) == 3
            warnings = get_data_quality_warnings(conn, int(user["id"]))
            assert isinstance(warnings, list)
            fire_year = estimate_fire_date(conn, int(user["id"]))
            assert fire_year is None or isinstance(fire_year, int)
            fire_scenario_id = str(uuid4())
            conn.execute(
                """
                INSERT INTO scenarios (id, user_id, name, scenario_type, inputs, outputs)
                VALUES (?, ?, ?, 'fire', ?, ?)
                """,
                (
                    fire_scenario_id,
                    int(user["id"]),
                    "Smoke FIRE",
                    json.dumps({"annual_spending": 42000}),
                    json.dumps({"net_worth_delta_final": 10000}),
                ),
            )
            conn.commit()
            fire_saved = conn.execute(
                "SELECT COUNT(*) FROM scenarios WHERE user_id = ? AND scenario_type = 'fire'",
                (int(user["id"]),),
            ).fetchone()[0]
            assert fire_saved == 1
            onboarding = get_onboarding_status(conn, int(user["id"]))
            assert onboarding["transaction_count"] >= 2
            assert onboarding["complete_count"] >= 1
            print("FIRE UI service OK")
        finally:
            conn.close()
    finally:
        db_module.DB_PATH = original_db_path
        Path(temp_db.name).unlink(missing_ok=True)

    print("All smoke tests passed.")


if __name__ == "__main__":
    main()

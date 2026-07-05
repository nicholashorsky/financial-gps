"""What-if scenario builder and comparison."""

from __future__ import annotations

import json
from uuid import uuid4

import pandas as pd
import streamlit as st

from budget.scenario_engine import SCENARIO_TYPES, ScenarioResult, run_scenario
from shared.db import get_connection


def _money(value: float) -> str:
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.2f}"


def _goal_delta_text(months: int) -> str:
    if months < 0:
        return f"{abs(months)} month(s) sooner"
    if months > 0:
        return f"{months} month(s) later"
    return "No material change"


def _save_scenario(conn, user_id: int, name: str, scenario_type: str, inputs: dict, result: ScenarioResult) -> str:
    scenario_id = str(uuid4())
    conn.execute(
        """
        INSERT INTO scenarios (id, user_id, name, scenario_type, inputs, outputs)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            scenario_id,
            user_id,
            name,
            scenario_type,
            json.dumps(inputs, sort_keys=True),
            json.dumps(result.to_dict(), sort_keys=True),
        ),
    )
    conn.commit()
    return scenario_id


def _load_scenarios(conn, user_id: int) -> list[dict]:
    rows = conn.execute(
        """
        SELECT id, name, scenario_type, inputs, outputs, created_at
        FROM scenarios
        WHERE user_id = ?
        ORDER BY created_at DESC
        """,
        (user_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def _render_result(result: ScenarioResult) -> None:
    cols = st.columns(3)
    cols[0].metric("Monthly cash flow", _money(result.monthly_cash_flow_delta))
    cols[1].metric("5-year net worth impact", _money(result.five_year_net_worth_impact))
    cols[2].metric("Goal date impact", _goal_delta_text(result.goal_date_delta_months))
    st.info(result.verdict)
    with st.expander("Scenario details"):
        st.json(result.details)


def _new_job_form() -> tuple[dict, bool]:
    current_salary = st.number_input("Current salary", min_value=0.0, value=80000.0, step=5000.0)
    new_salary = st.number_input("New salary", min_value=0.0, value=95000.0, step=5000.0)
    commute_cost_change = st.number_input("Monthly commute cost change", value=0.0, step=50.0)
    benefits_value_change = st.number_input("Annual benefits value change", value=0.0, step=500.0)
    remote_work_savings = st.number_input("Monthly remote work savings", min_value=0.0, value=0.0, step=50.0)
    tax_rate = st.slider("Marginal tax estimate", min_value=0.0, max_value=0.60, value=0.30, step=0.01)
    return {
        "current_salary": current_salary,
        "new_salary": new_salary,
        "commute_cost_change": commute_cost_change,
        "benefits_value_change": benefits_value_change,
        "remote_work_savings": remote_work_savings,
        "tax_rate": tax_rate,
    }, True


def _buy_house_form() -> tuple[dict, bool]:
    purchase_price = st.number_input("Purchase price", min_value=0.0, value=650000.0, step=25000.0)
    down_payment_pct = st.slider("Down payment %", min_value=0.0, max_value=100.0, value=20.0, step=1.0)
    mortgage_rate = st.slider("Mortgage rate %", min_value=0.0, max_value=15.0, value=5.0, step=0.1)
    amortization_years = st.slider("Amortization years", min_value=5, max_value=30, value=25)
    property_tax_annual = st.number_input("Property tax annual", min_value=0.0, value=4500.0, step=250.0)
    maintenance_pct = st.slider("Maintenance reserve %", min_value=0.0, max_value=5.0, value=1.0, step=0.1)
    current_rent = st.number_input("Current monthly rent", min_value=0.0, value=2500.0, step=100.0)
    return {
        "purchase_price": purchase_price,
        "down_payment_pct": down_payment_pct,
        "mortgage_rate": mortgage_rate,
        "amortization_years": amortization_years,
        "property_tax_annual": property_tax_annual,
        "maintenance_pct": maintenance_pct,
        "current_rent": current_rent,
    }, True


def _side_hustle_form() -> tuple[dict, bool]:
    monthly_revenue = st.number_input("Monthly revenue", min_value=0.0, value=1500.0, step=100.0)
    monthly_expenses = st.number_input("Monthly expenses", min_value=0.0, value=300.0, step=50.0)
    growth_rate = st.slider("Annual growth %", min_value=0.0, max_value=100.0, value=10.0, step=1.0)
    tax_rate = st.slider("Self-employment tax estimate %", min_value=0.0, max_value=60.0, value=30.0, step=1.0)
    return {
        "monthly_revenue": monthly_revenue,
        "monthly_expenses": monthly_expenses,
        "growth_rate": growth_rate,
        "tax_rate": tax_rate,
    }, True


def _major_purchase_form() -> tuple[dict, bool]:
    purchase_price = st.number_input("Purchase price", min_value=0.0, value=12000.0, step=500.0)
    cash_paid = st.number_input("Cash paid upfront", min_value=0.0, value=3000.0, step=500.0)
    financing_rate = st.slider("Financing rate %", min_value=0.0, max_value=35.0, value=8.0, step=0.5)
    financing_term_months = st.slider("Financing term months", min_value=0, max_value=84, value=36)
    return {
        "purchase_price": purchase_price,
        "cash_paid": cash_paid,
        "financing_rate": financing_rate,
        "financing_term_months": financing_term_months,
    }, True


def _builder_for(scenario_type: str) -> tuple[dict, bool]:
    builders = {
        "new_job": _new_job_form,
        "buy_house": _buy_house_form,
        "side_hustle": _side_hustle_form,
        "major_purchase": _major_purchase_form,
    }
    return builders[scenario_type]()


def _render_saved_scenarios(conn, user_id: int) -> None:
    rows = _load_scenarios(conn, user_id)
    if not rows:
        st.info("No saved scenarios yet.")
        return

    comparison_rows = []
    for row in rows:
        outputs = json.loads(row["outputs"] or "{}")
        comparison_rows.append(
            {
                "Name": row["name"],
                "Type": SCENARIO_TYPES.get(row["scenario_type"], row["scenario_type"]),
                "Monthly delta": outputs.get("monthly_cash_flow_delta", 0),
                "5-year impact": outputs.get("five_year_net_worth_impact", 0),
                "Goal date": _goal_delta_text(int(outputs.get("goal_date_delta_months", 0))),
                "Created": row["created_at"],
            }
        )

    st.dataframe(pd.DataFrame(comparison_rows), use_container_width=True, hide_index=True)

    for row in rows[:5]:
        outputs = json.loads(row["outputs"] or "{}")
        with st.expander(row["name"]):
            st.write(outputs.get("verdict", "Saved scenario."))
            st.json({"inputs": json.loads(row["inputs"] or "{}"), "outputs": outputs})


def render() -> None:
    st.title("Scenarios")
    st.caption("Ask a what-if, see the cash-flow consequence, save the ones worth watching.")

    user = st.session_state.get("user")
    if not user:
        st.info("Log in to build scenarios.")
        return

    user_id = int(user["id"])
    conn = get_connection()
    try:
        build_tab, saved_tab = st.tabs(["Build", "Saved"])
        with build_tab:
            scenario_type = st.selectbox(
                "Scenario type",
                options=list(SCENARIO_TYPES.keys()),
                format_func=lambda key: SCENARIO_TYPES[key],
            )
            scenario_name = st.text_input("Scenario name", value=SCENARIO_TYPES[scenario_type])
            inputs, valid = _builder_for(scenario_type)
            result = run_scenario(scenario_type, inputs)

            st.divider()
            _render_result(result)

            if st.button("Save scenario", type="primary", use_container_width=True, disabled=not valid):
                _save_scenario(conn, user_id, scenario_name.strip() or SCENARIO_TYPES[scenario_type], scenario_type, inputs, result)
                st.success("Saved. Future You is watching this one closely.")

        with saved_tab:
            st.subheader("Saved Scenario Comparison")
            _render_saved_scenarios(conn, user_id)
    finally:
        conn.close()

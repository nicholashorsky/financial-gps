"""FIRE scenario builder and side-by-side comparison."""

from __future__ import annotations

import json
from uuid import uuid4

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from fire_engine.engine.scenario import clone_household_with_overrides, compare_scenarios
from shared.db import get_connection
from shared.fire_service import build_household


def _save_fire_scenario(conn, user_id: int, name: str, inputs: dict, outputs: dict) -> None:
    conn.execute(
        """
        INSERT INTO scenarios (id, user_id, name, scenario_type, inputs, outputs)
        VALUES (?, ?, ?, 'fire', ?, ?)
        """,
        (str(uuid4()), user_id, name, json.dumps(inputs, sort_keys=True), json.dumps(outputs, sort_keys=True)),
    )
    conn.commit()


def _saved_fire_scenarios(conn, user_id: int) -> list[dict]:
    rows = conn.execute(
        """
        SELECT id, name, inputs, outputs, created_at
        FROM scenarios
        WHERE user_id = ? AND scenario_type = 'fire'
        ORDER BY created_at DESC
        """,
        (user_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def render() -> None:
    st.title("FIRE Scenarios")
    st.caption("Clone the current plan, nudge the assumptions, and compare the ending in numbers rather than mood.")

    user = st.session_state.get("user")
    if not user:
        st.info("Log in to build FIRE scenarios.")
        return

    user_id = int(user["id"])
    conn = get_connection()
    try:
        household = build_household(conn, user_id)
        if household is None:
            st.warning("Complete the FIRE profile before comparing FIRE scenarios.")
            return

        tabs = st.tabs(["Build", "Saved"])
        with tabs[0]:
            scenario_name = st.text_input("Scenario name", value="FIRE variant")
            left, right = st.columns(2)
            with left:
                annual_spending = st.number_input("Scenario annual spending", min_value=0.0, value=float(household.annual_spending), step=1000.0)
                extra_income = st.number_input("Extra annual income", value=0.0, step=1000.0)
            with right:
                extra_assets = st.number_input("Extra starting assets", value=0.0, step=1000.0)
                spending_inflation = st.slider("Spending inflation", min_value=0.0, max_value=0.08, value=float(household.spending_inflation), step=0.005)

            scenario_household = clone_household_with_overrides(
                household,
                annual_spending=annual_spending,
                spending_inflation=spending_inflation,
                extra_income=extra_income,
                extra_starting_assets=extra_assets,
            )
            comparison = compare_scenarios(household, scenario_household, years=40)
            base_projection = comparison["base"]
            scenario_projection = comparison["scenario"]

            metrics = st.columns(3)
            metrics[0].metric("Final net worth delta", f"${comparison['net_worth_delta_final']:,.2f}")
            metrics[1].metric("First-year surplus delta", f"${comparison['surplus_delta_first_year']:,.2f}")
            metrics[2].metric("Scenario final net worth", f"${scenario_projection[-1].net_worth:,.2f}")

            comparison_frame = pd.DataFrame(
                {
                    "Year": [year.year for year in base_projection],
                    "Base net worth": [year.net_worth for year in base_projection],
                    "Scenario net worth": [year.net_worth for year in scenario_projection],
                }
            )
            chart = go.Figure()
            chart.add_trace(go.Scatter(x=comparison_frame["Year"], y=comparison_frame["Base net worth"], mode="lines", name="Base"))
            chart.add_trace(go.Scatter(x=comparison_frame["Year"], y=comparison_frame["Scenario net worth"], mode="lines", name="Scenario"))
            chart.update_layout(height=380, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(chart, use_container_width=True)
            st.dataframe(comparison_frame, use_container_width=True, hide_index=True)

            if st.button("Save FIRE scenario", type="primary", use_container_width=True):
                _save_fire_scenario(
                    conn,
                    user_id,
                    scenario_name.strip() or "FIRE scenario",
                    {
                        "annual_spending": annual_spending,
                        "extra_income": extra_income,
                        "extra_starting_assets": extra_assets,
                        "spending_inflation": spending_inflation,
                    },
                    {
                        "net_worth_delta_final": comparison["net_worth_delta_final"],
                        "surplus_delta_first_year": comparison["surplus_delta_first_year"],
                        "scenario_final_net_worth": scenario_projection[-1].net_worth,
                    },
                )
                st.success("FIRE scenario saved.")

        with tabs[1]:
            saved = _saved_fire_scenarios(conn, user_id)
            if not saved:
                st.info("No saved FIRE scenarios yet.")
            else:
                rows = []
                for row in saved:
                    outputs = json.loads(row["outputs"] or "{}")
                    rows.append(
                        {
                            "Name": row["name"],
                            "Final net worth delta": outputs.get("net_worth_delta_final", 0),
                            "First-year surplus delta": outputs.get("surplus_delta_first_year", 0),
                            "Scenario final net worth": outputs.get("scenario_final_net_worth", 0),
                            "Created": row["created_at"],
                        }
                    )
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    finally:
        conn.close()

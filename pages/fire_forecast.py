"""40-year FIRE projection with drillable year-by-year breakdown."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from budget.narrator import fire_date_message
from shared.db import get_connection
from shared.fire_service import estimate_fire_date, get_data_quality_warnings, project_user_household


def render() -> None:
    st.title("FIRE Forecast")
    st.caption("A deterministic 40-year view built from your current income, benefit elections, accounts, and spending baseline.")

    user = st.session_state.get("user")
    if not user:
        st.info("Log in to run a FIRE forecast.")
        return

    user_id = int(user["id"])
    conn = get_connection()
    try:
        projection = project_user_household(conn, user_id, years=40)
        if not projection:
            st.warning("Complete your FIRE profile and benefit elections before running the forecast.")
            left, right = st.columns(2)
            if left.button("Open Financial Profile", use_container_width=True):
                st.session_state.page = "Financial Profile"
                st.rerun()
            if right.button("Open Benefits Workspace", use_container_width=True):
                st.session_state.page = "Benefits Workspace"
                st.rerun()
            return

        frame = pd.DataFrame(
            [
                {
                    "Year": year.year,
                    "Age": year.age,
                    "Employment": year.employment_income,
                    "CPP": year.cpp_received,
                    "OAS": year.oas_received,
                    "GIS": year.gis_received,
                    "Federal tax": year.federal_tax,
                    "Ontario tax": year.provincial_tax,
                    "Taxable income": year.taxable_income,
                    "Withdrawals": sum(year.withdrawals.values()),
                    "Taxable withdrawals": year.taxable_withdrawals,
                    "RRIF minimum": year.rrif_minimum_withdrawal,
                    "RRIF balance": year.account_balances.get("rrif", 0.0),
                    "Tax parameters": year.parameter_year,
                    "Spending": year.total_spending,
                    "Net surplus": year.net_surplus,
                    "Net worth": year.net_worth,
                    "Rules": ", ".join(year.triggered_rules),
                    "Sequencer": "; ".join(year.sequencer_notes),
                }
                for year in projection
            ]
        )

        chart = go.Figure()
        chart.add_trace(go.Scatter(x=frame["Year"], y=frame["Net worth"], mode="lines", name="Net worth"))
        chart.update_layout(height=420, margin=dict(l=20, r=20, t=20, b=20), yaxis_title="Net worth")
        st.plotly_chart(chart, use_container_width=True)
        st.info(fire_date_message(estimate_fire_date(conn, user_id)))

        if any(year.uses_parameter_fallback for year in projection):
            st.info(
                "Forecast years without verified CRA parameters use flat 2026 "
                "tax and benefit values. This assumption is shown in the year-by-year table."
            )

        warnings = [
            warning
            for warning in get_data_quality_warnings(conn, user_id)
            if warning.code != "tax_parameter_fallback"
        ]
        if warnings:
            for warning in warnings[:4]:
                st.warning(warning.message)

        st.subheader("Year-by-year detail")
        st.dataframe(frame, use_container_width=True, hide_index=True)
    finally:
        conn.close()

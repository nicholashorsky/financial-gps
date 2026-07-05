"""Basic 30-year 3-band forecast."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from budget.narrator import forecast_message
from shared.db import get_connection


def _current_net_worth(conn, user_id: int) -> float:
    rows = conn.execute(
        """
        SELECT COALESCE(SUM(balance), 0) AS total
        FROM accounts
        WHERE user_id = ?
        """,
        (user_id,),
    ).fetchone()
    return float(rows["total"] or 0)


def _annual_projection(start_value: float, yearly_contrib: float, years: int, annual_return: float) -> list[float]:
    values = []
    balance = start_value
    monthly_return = (1 + annual_return) ** (1 / 12) - 1
    monthly_contrib = yearly_contrib / 12
    for month in range(1, years * 12 + 1):
        balance = balance * (1 + monthly_return) + monthly_contrib
        if month % 12 == 0:
            values.append(round(balance, 2))
    return values


def _projection_frame(start_value: float, yearly_contrib: float, years: int, rate: float, label: str) -> pd.DataFrame:
    yearly_values = _annual_projection(start_value, yearly_contrib, years, rate)
    return pd.DataFrame(
        {
            "Year": list(range(1, years + 1)),
            label: yearly_values,
        }
    )


def _milestones(values: pd.DataFrame, label: str, targets: list[float]) -> list[tuple[float, float]]:
    markers: list[tuple[float, float]] = []
    for target in targets:
        hit = values[values[label] >= target].head(1)
        if not hit.empty:
            year = float(hit.iloc[0]["Year"])
            markers.append((year, target))
    return markers


def render() -> None:
    st.title("Forecast")
    st.caption("A plain-language 30-year projection with three bands and a few honest assumptions.")

    user = st.session_state.get("user")
    if not user:
        st.info("Log in to see your forecast.")
        return

    user_id = int(user["id"])
    conn = get_connection()
    try:
        net_worth = _current_net_worth(conn, user_id)
        summary_row = conn.execute(
            """
            SELECT
                COALESCE(SUM(CASE WHEN amount > 0 AND is_excluded = 0 THEN amount ELSE 0 END), 0) AS income_total,
                COALESCE(SUM(CASE WHEN amount < 0 AND is_excluded = 0 THEN ABS(amount) ELSE 0 END), 0) AS spending_total
            FROM transactions
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()
        monthly_surplus = float(summary_row["income_total"] or 0) - float(summary_row["spending_total"] or 0)

        st.subheader("Assumptions")
        col1, col2, col3 = st.columns(3)
        conservative_return = col1.slider("Conservative return", 0.0, 0.12, 0.04, 0.005)
        expected_return = col2.slider("Expected return", 0.0, 0.15, 0.06, 0.005)
        optimistic_return = col3.slider("Optimistic return", 0.0, 0.18, 0.08, 0.005)
        income_growth = st.slider("Annual income growth", 0.0, 0.1, 0.03, 0.005)
        inflation = st.slider("Inflation", 0.0, 0.08, 0.025, 0.005)
        years = st.slider("Projection horizon (years)", 10, 40, 30)

        yearly_contrib = max(monthly_surplus, 0) * 12
        adjusted_expected_contrib = yearly_contrib * ((1 + income_growth) ** 0.5)
        if monthly_surplus < 0:
            adjusted_expected_contrib = monthly_surplus * 12

        conservative = _projection_frame(net_worth, yearly_contrib * (1 - inflation), years, conservative_return, "Conservative")
        expected = _projection_frame(net_worth, adjusted_expected_contrib, years, expected_return, "Expected")
        optimistic = _projection_frame(net_worth, yearly_contrib * (1 + income_growth), years, optimistic_return, "Optimistic")

        frame = conservative.merge(expected, on="Year").merge(optimistic, on="Year")

        figure = go.Figure()
        figure.add_trace(go.Scatter(x=frame["Year"], y=frame["Conservative"], name="Conservative", mode="lines"))
        figure.add_trace(go.Scatter(x=frame["Year"], y=frame["Expected"], name="Expected", mode="lines"))
        figure.add_trace(go.Scatter(x=frame["Year"], y=frame["Optimistic"], name="Optimistic", mode="lines"))
        figure.update_layout(
            title="30-Year Net Worth Projection",
            height=420,
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis_title="Year",
            yaxis_title="Net Worth",
        )
        for year, target in _milestones(frame, "Expected", [250000, 500000, 1000000]):
            figure.add_vline(x=year, line_width=1, line_dash="dot", line_color="#94a3b8")
            figure.add_annotation(x=year, y=target, text=f"${target:,.0f}", showarrow=True, arrowhead=1, yshift=10)

        st.plotly_chart(figure, use_container_width=True)
        conservative_horizon = next(
            (int(year) for year, target in _milestones(frame, "Expected", [100000]) if target == 100000),
            None,
        )
        st.info(forecast_message(monthly_surplus, conservative_horizon))

        st.subheader("Yearly Snapshot")
        st.dataframe(frame, use_container_width=True, hide_index=True)

        st.caption("For a Canada-specific FIRE projection, open the FIRE Planner →")
    finally:
        conn.close()

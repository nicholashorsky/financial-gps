"""Basic 30-year 3-band forecast."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from budget.narrator import forecast_message
from shared.db import get_connection


BAND_EXPLANATIONS = {
    "Conservative": "Lower return; positive cash flow is reduced by inflation, while a deficit is increased by it.",
    "Expected": "Expected return; uses the current cash-flow trend with the existing income-growth adjustment.",
    "Optimistic": "Higher return; positive cash flow is increased by income growth, while a deficit is reduced by it.",
}


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


def _monthly_cash_flow(conn, user_id: int) -> tuple[float, int]:
    """Return average monthly cash flow and the number of usable observed months."""

    row = conn.execute(
        """
        SELECT
            COUNT(DISTINCT SUBSTR(date, 1, 7)) AS observed_months,
            COALESCE(SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END), 0) AS income_total,
            COALESCE(SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END), 0) AS spending_total
        FROM transactions
        WHERE user_id = ?
          AND is_excluded = 0
          AND COALESCE(category, '') <> 'Transfer'
          AND COALESCE(transaction_type, '') NOT IN ('transfer', 'transfer_in', 'transfer_out')
        """,
        (user_id,),
    ).fetchone()
    observed_months = int(row["observed_months"] or 0)
    if observed_months == 0:
        return 0.0, 0
    total_cash_flow = float(row["income_total"] or 0) - float(row["spending_total"] or 0)
    return total_cash_flow / observed_months, observed_months


def _forecast_state(net_worth: float, observed_months: int) -> str:
    return "needs_setup" if net_worth == 0 and observed_months == 0 else "configured"


def _band_contributions(monthly_surplus: float, income_growth: float, inflation: float) -> dict[str, float]:
    """Return fixed annual cash-flow assumptions while preserving positive-case behavior."""

    annual_cash_flow = monthly_surplus * 12
    if annual_cash_flow >= 0:
        return {
            "Conservative": annual_cash_flow * (1 - inflation),
            "Expected": annual_cash_flow * ((1 + income_growth) ** 0.5),
            "Optimistic": annual_cash_flow * (1 + income_growth),
        }
    return {
        "Conservative": annual_cash_flow * (1 + inflation),
        "Expected": annual_cash_flow,
        "Optimistic": annual_cash_flow * max(1 - income_growth, 0),
    }


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
        monthly_surplus, observed_months = _monthly_cash_flow(conn, user_id)

        if _forecast_state(net_worth, observed_months) == "needs_setup":
            st.warning(
                "Your forecast needs a starting balance or transaction history before its lines mean anything. "
                "Import transactions and review account balances in Spending."
            )
            if st.button("Set up forecast inputs", type="primary"):
                st.session_state.page = "Spending"
                st.rerun()
            return

        metric_left, metric_right = st.columns(2)
        metric_left.metric("Starting net worth", f"${net_worth:,.0f}")
        metric_right.metric("Average monthly cash flow", f"${monthly_surplus:,.0f}")
        if observed_months:
            st.caption(
                f"Cash flow is the average of {observed_months} imported month{'s' if observed_months != 1 else ''}; "
                "excluded transactions and transfers are not counted."
            )
        else:
            st.info("No usable transaction history was found, so this is a balance-growth-only forecast.")

        st.subheader("Assumptions")
        col1, col2, col3 = st.columns(3)
        conservative_return = col1.slider("Conservative return", 0.0, 0.12, 0.04, 0.005)
        expected_return = col2.slider("Expected return", 0.0, 0.15, 0.06, 0.005)
        optimistic_return = col3.slider("Optimistic return", 0.0, 0.18, 0.08, 0.005)
        income_growth = st.slider("Annual income growth", 0.0, 0.1, 0.03, 0.005)
        inflation = st.slider("Inflation", 0.0, 0.08, 0.025, 0.005)
        years = st.slider("Projection horizon (years)", 10, 40, 30)

        returns = {
            "Conservative": conservative_return,
            "Expected": expected_return,
            "Optimistic": optimistic_return,
        }
        contributions = _band_contributions(monthly_surplus, income_growth, inflation)
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Band": band,
                        "Annual return": f"{returns[band]:.1%}",
                        "Annual cash flow": f"${contributions[band]:,.0f}",
                        "How it differs": BAND_EXPLANATIONS[band],
                    }
                    for band in ("Conservative", "Expected", "Optimistic")
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )

        conservative = _projection_frame(
            net_worth, contributions["Conservative"], years, conservative_return, "Conservative"
        )
        expected = _projection_frame(net_worth, contributions["Expected"], years, expected_return, "Expected")
        optimistic = _projection_frame(
            net_worth, contributions["Optimistic"], years, optimistic_return, "Optimistic"
        )

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
        if monthly_surplus < 0:
            st.warning(
                "This projection declines because your imported spending currently exceeds imported income. "
                "All three bands continue that shortfall. Values below $0 represent projected net debt, not a missing forecast line."
            )
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

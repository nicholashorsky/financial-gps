"""Home dashboard - lightweight summary and onboarding nudge."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from budget.importer import get_spending_summary
from budget.narrator import fire_date_message, home_message, no_goals_message
from shared.db import get_connection
from shared.fire_service import estimate_fire_date
from shared.formatting import format_currency, format_month
from shared.onboarding_service import get_onboarding_status
from shared.theme import INCOME, SPENDING, style_figure
from shared.ui import empty_state, page_header


def _goal_stats(conn, user_id: int) -> tuple[int, float, float, list[dict]]:
    rows = conn.execute(
        """
        SELECT id, name, target_amount, current_amount, monthly_contribution, target_date, goal_type
        FROM goals
        WHERE user_id = ?
        ORDER BY COALESCE(target_date, '9999-12-31') ASC, id ASC
        """,
        (user_id,),
    ).fetchall()
    goals = [dict(row) for row in rows]
    total_target = sum(float(goal["target_amount"] or 0) for goal in goals)
    total_current = sum(float(goal["current_amount"] or 0) for goal in goals)
    return len(goals), total_target, total_current, goals


def _monthly_sparkline(conn, user_id: int) -> pd.DataFrame:
    rows = conn.execute(
        """
        SELECT substr(date, 1, 7) AS month,
               COALESCE(SUM(CASE WHEN amount < 0 AND is_excluded = 0 AND COALESCE(category, '') <> 'Transfer' THEN ABS(amount) ELSE 0 END), 0) AS spending,
               COALESCE(SUM(CASE WHEN amount > 0 AND is_excluded = 0 AND COALESCE(category, '') <> 'Transfer' THEN amount ELSE 0 END), 0) AS income
        FROM transactions
        WHERE user_id = ?
        GROUP BY substr(date, 1, 7)
        ORDER BY month ASC
        """,
        (user_id,),
    ).fetchall()
    return pd.DataFrame([dict(row) for row in rows])


def render() -> None:
    page_header("Home", "A quick read on where things stand before we get fancier.")

    user = st.session_state.get("user")
    if not user:
        st.info("Log in to see your financial snapshot.")
        return

    user_id = int(user["id"])
    conn = get_connection()
    try:
        summary = get_spending_summary(conn, user_id)
        onboarding = get_onboarding_status(conn, user_id)
        goal_count, total_target, total_current, goals = _goal_stats(conn, user_id)
        savings_rate = (summary.income_total - summary.spending_total) / summary.income_total if summary.income_total else 0
        months_to_next_goal = None
        if goals:
            next_goal = next(
                (
                    goal
                    for goal in goals
                    if float(goal["target_amount"] or 0) > float(goal["current_amount"] or 0)
                ),
                None,
            )
            if next_goal:
                monthly_contribution = float(next_goal["monthly_contribution"] or 0)
                if monthly_contribution > 0:
                    remaining = max(float(next_goal["target_amount"] or 0) - float(next_goal["current_amount"] or 0), 0)
                    months_to_next_goal = int((remaining + monthly_contribution - 1) // monthly_contribution)

        fire_year = estimate_fire_date(conn, user_id)
        primary_metrics = st.columns(3)
        primary_metrics[0].metric("Transactions", summary.transaction_count)
        primary_metrics[1].metric("Savings rate", f"{savings_rate:.1%}")
        primary_metrics[2].metric(
            "Monthly surplus",
            format_currency(summary.income_total - summary.spending_total),
        )

        planning_metrics = st.columns(2)
        planning_metrics[0].metric(
            "Months to next goal",
            months_to_next_goal if months_to_next_goal is not None else "n/a",
        )
        planning_metrics[1].metric(
            "FIRE date",
            fire_year if fire_year is not None else "n/a",
        )

        if summary.transaction_count == 0:
            empty_state(
                "No CSV has been imported yet. Open Spending to load bank data and wake up the dashboards.",
                action_label="Go to Onboarding",
                on_action=lambda: setattr(st.session_state, "page", "Onboarding"),
            )
            return

        st.divider()
        left, right = st.columns([1.2, 1])
        with left:
            st.subheader("Twelve Month Snapshot")
            spark = _monthly_sparkline(conn, user_id)
            if spark.empty:
                st.info("Monthly trend appears after a few imports.")
            else:
                figure = go.Figure()
                month_labels = [format_month(month) for month in spark["month"]]
                figure.add_trace(go.Scatter(x=month_labels, y=spark["income"], name="Income", mode="lines+markers", line_color=INCOME))
                figure.add_trace(go.Scatter(x=month_labels, y=spark["spending"], name="Spending", mode="lines+markers", line_color=SPENDING))
                style_figure(figure)
                figure.update_xaxes(type="category")
                st.plotly_chart(figure, use_container_width=True)

        with right:
            st.subheader("Narrator")
            top_category = None
            if summary.spending_by_category:
                top_category = summary.spending_by_category[0]["category"]
            st.info(home_message(summary.transaction_count, goal_count))
            st.caption(
                f"Tracked goals: {goal_count} | Goal capital: {format_currency(total_current)} / {format_currency(total_target)}"
            )
            st.caption(
                f"Setup progress: {onboarding['complete_count']} of {len(onboarding['steps'])} core steps complete"
            )
            st.caption(fire_date_message(fire_year))
            if top_category:
                st.caption(f"Top spending category: {top_category}")

        st.divider()
        st.subheader("Goal Progress")
        if not goals:
            st.info(no_goals_message())
        else:
            for goal in goals[:3]:
                target = float(goal["target_amount"] or 0)
                current = float(goal["current_amount"] or 0)
                progress = 0.0 if target <= 0 else min(current / target, 1.0)
                st.progress(progress, text=f"{goal['name']} - {progress:.0%}")
    finally:
        conn.close()

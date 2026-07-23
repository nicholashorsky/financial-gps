"""Financial goals CRUD."""

from __future__ import annotations

from datetime import date
import pandas as pd
import streamlit as st

from budget.narrator import goal_message, no_goals_message
from shared.db import get_connection


GOAL_TYPES = ["emergency", "house", "vacation", "retirement", "other"]


def _load_goals(conn, user_id: int) -> list[dict]:
    rows = conn.execute(
        """
        SELECT id, name, target_amount, current_amount, monthly_contribution, target_date, goal_type
        FROM goals
        WHERE user_id = ?
        ORDER BY COALESCE(target_date, '9999-12-31') ASC, id ASC
        """,
        (user_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def _months_to_target(target_date: str | None) -> int | None:
    if not target_date:
        return None
    try:
        target = date.fromisoformat(target_date)
    except ValueError:
        return None
    today = date.today()
    months = (target.year - today.year) * 12 + (target.month - today.month)
    return max(months, 0)


def _required_monthly(goal: dict) -> float | None:
    months = _months_to_target(goal.get("target_date"))
    if not months:
        return None
    remaining = max(float(goal.get("target_amount") or 0) - float(goal.get("current_amount") or 0), 0)
    return round(remaining / months, 2) if months > 0 else remaining


def _progress(goal: dict) -> float:
    target = float(goal.get("target_amount") or 0)
    current = float(goal.get("current_amount") or 0)
    return 0.0 if target <= 0 else min((current / target) * 100.0, 100.0)


def _render_goal_card(goal: dict, user_id: int, conn) -> None:
    progress = _progress(goal)
    st.progress(progress / 100.0, text=f"{goal['name']} - {progress:.0f}%")
    st.caption(goal_message(goal["name"], progress))

    cols = st.columns([1.1, 1, 1, 0.7])
    cols[0].write(f"Target: ${float(goal.get('target_amount') or 0):,.2f}")
    cols[1].write(f"Current: ${float(goal.get('current_amount') or 0):,.2f}")
    required = _required_monthly(goal)
    cols[2].write(
        "Required/month: " + (f"${required:,.2f}" if required is not None else "Set a target date")
    )
    if cols[3].button("Delete", key=f"delete_goal_{goal['id']}"):
        conn.execute("DELETE FROM goals WHERE id = ? AND user_id = ?", (goal["id"], user_id))
        conn.commit()
        st.rerun()


def render() -> None:
    st.title("Goals")
    st.caption("Set targets, update progress, and see the monthly number that keeps showing up.")

    user = st.session_state.get("user")
    if not user:
        st.info("Log in to manage goals.")
        return

    user_id = int(user["id"])
    conn = get_connection()
    try:
        goals = _load_goals(conn, user_id)
        total_target = sum(float(goal["target_amount"] or 0) for goal in goals)
        total_current = sum(float(goal["current_amount"] or 0) for goal in goals)

        progress_metrics = st.columns(2)
        progress_metrics[0].metric("Goals", len(goals))
        progress_metrics[1].metric("Tracked", f"${total_current:,.2f}")
        st.metric("Targeted", f"${total_target:,.2f}")

        st.divider()
        st.subheader("Create Goal")
        with st.form("goal_create_form", clear_on_submit=True):
            name = st.text_input("Name")
            target_amount = st.number_input("Target amount", min_value=0.0, value=1000.0, step=100.0)
            current_amount = st.number_input("Current amount", min_value=0.0, value=0.0, step=100.0)
            monthly_contribution = st.number_input("Monthly contribution", min_value=0.0, value=0.0, step=50.0)
            target_date = st.date_input("Target date", value=date.today())
            goal_type = st.selectbox("Goal type", GOAL_TYPES)
            submitted = st.form_submit_button("Add goal", type="primary")
            if submitted:
                if not name.strip():
                    st.error("Goal name is required.")
                else:
                    conn.execute(
                        """
                        INSERT INTO goals (user_id, name, target_amount, current_amount, monthly_contribution, target_date, goal_type)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            user_id,
                            name.strip(),
                            target_amount,
                            current_amount,
                            monthly_contribution,
                            target_date.isoformat(),
                            goal_type,
                        ),
                    )
                    conn.commit()
                    st.rerun()

        st.divider()
        st.subheader("Your Goals")
        if not goals:
            st.info(no_goals_message())
        else:
            for goal in goals:
                with st.container(border=True):
                    _render_goal_card(goal, user_id, conn)

                    with st.expander("Edit"):
                        with st.form(f"edit_goal_{goal['id']}"):
                            edit_name = st.text_input("Name", value=goal["name"], key=f"goal_name_{goal['id']}")
                            edit_target = st.number_input(
                                "Target amount",
                                min_value=0.0,
                                value=float(goal["target_amount"] or 0),
                                step=100.0,
                                key=f"goal_target_{goal['id']}",
                            )
                            edit_current = st.number_input(
                                "Current amount",
                                min_value=0.0,
                                value=float(goal["current_amount"] or 0),
                                step=100.0,
                                key=f"goal_current_{goal['id']}",
                            )
                            edit_monthly = st.number_input(
                                "Monthly contribution",
                                min_value=0.0,
                                value=float(goal["monthly_contribution"] or 0),
                                step=50.0,
                                key=f"goal_monthly_{goal['id']}",
                            )
                            current_target_date = date.fromisoformat(goal["target_date"]) if goal["target_date"] else date.today()
                            edit_target_date = st.date_input(
                                "Target date",
                                value=current_target_date,
                                key=f"goal_date_{goal['id']}",
                            )
                            edit_goal_type = st.selectbox(
                                "Goal type",
                                GOAL_TYPES,
                                index=GOAL_TYPES.index(goal["goal_type"]) if goal["goal_type"] in GOAL_TYPES else len(GOAL_TYPES) - 1,
                                key=f"goal_type_{goal['id']}",
                            )
                            if st.form_submit_button("Save changes", type="primary"):
                                conn.execute(
                                    """
                                    UPDATE goals
                                    SET name = ?, target_amount = ?, current_amount = ?,
                                        monthly_contribution = ?, target_date = ?, goal_type = ?
                                    WHERE id = ? AND user_id = ?
                                    """,
                                    (
                                        edit_name.strip(),
                                        edit_target,
                                        edit_current,
                                        edit_monthly,
                                        edit_target_date.isoformat(),
                                        edit_goal_type,
                                        goal["id"],
                                        user_id,
                                    ),
                                )
                                conn.commit()
                                st.rerun()

        if goals:
            st.divider()
            st.subheader("Goal Overview")
            overview = pd.DataFrame(
                [
                    {
                        "Goal": goal["name"],
                        "Progress %": round(_progress(goal), 1),
                        "Required / month": _required_monthly(goal),
                        "Target date": goal["target_date"],
                    }
                    for goal in goals
                ]
            )
            st.dataframe(overview, use_container_width=True, hide_index=True)
    finally:
        conn.close()

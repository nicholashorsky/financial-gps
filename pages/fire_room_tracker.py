"""TFSA / RRSP / FHSA room tracker."""

from __future__ import annotations

from datetime import date

import streamlit as st

from shared.db import get_connection
from shared.fire_service import (
    calculate_room_snapshots,
    get_or_create_fhsa_state,
    get_or_create_rrsp_state,
    get_or_create_tfsa_state,
    save_fhsa_state,
    save_rrsp_state,
    save_tfsa_state,
)


def render() -> None:
    st.title("FIRE Planner - Account Room Tracker")
    st.caption("Room values are editable snapshots. They should agree with CRA or provider records when you have them.")

    user = st.session_state.get("user")
    if not user:
        st.info("Log in to track registered account room.")
        return

    user_id = int(user["id"])
    conn = get_connection()
    try:
        tfsa = get_or_create_tfsa_state(conn, user_id)
        rrsp = get_or_create_rrsp_state(conn, user_id)
        fhsa = get_or_create_fhsa_state(conn, user_id)
        snapshots = calculate_room_snapshots(conn, user_id)

        cols = st.columns(3)
        cols[0].metric("TFSA room", f"${snapshots['tfsa'].available_room:,.2f}")
        cols[1].metric("RRSP room", f"${snapshots['rrsp'].contribution_room_after_ytd:,.2f}")
        cols[2].metric("FHSA room", f"${snapshots['fhsa'].available_room:,.2f}")

        with st.form("room_tracker_form"):
            left, middle, right = st.columns(3)
            with left:
                st.markdown("**TFSA**")
                tfsa_year = st.number_input("Snapshot year", min_value=2009, value=int(tfsa.get("snapshot_year") or date.today().year), key="tfsa_year")
                tfsa_unused = st.number_input("Prior unused room", min_value=0.0, value=float(tfsa.get("prior_unused_room") or 0), step=100.0)
                tfsa_withdrawals = st.number_input("Prior year withdrawals", min_value=0.0, value=float(tfsa.get("prior_year_withdrawals") or 0), step=100.0)
                tfsa_ytd = st.number_input("YTD contributions", min_value=0.0, value=float(tfsa.get("ytd_contributions") or 0), step=100.0)
                tfsa_non_resident = st.checkbox("Was non-resident", value=bool(tfsa.get("was_non_resident", 0)))
            with middle:
                st.markdown("**RRSP**")
                rrsp_year = st.number_input("RRSP snapshot year", min_value=2000, value=int(rrsp.get("snapshot_year") or date.today().year), key="rrsp_year")
                rrsp_unused = st.number_input("Prior unused room", min_value=0.0, value=float(rrsp.get("prior_unused_room") or 0), step=100.0, key="rrsp_unused")
                rrsp_income = st.number_input("Prior year earned income", min_value=0.0, value=float(rrsp.get("prior_year_earned_income") or 0), step=500.0)
                rrsp_pa = st.number_input("Pension adjustment", min_value=0.0, value=float(rrsp.get("pension_adjustment") or 0), step=100.0)
                rrsp_ytd = st.number_input("YTD contributions", min_value=0.0, value=float(rrsp.get("ytd_contributions") or 0), step=100.0, key="rrsp_ytd")
            with right:
                st.markdown("**FHSA**")
                fhsa_open = st.date_input("Open date", value=date.fromisoformat(fhsa["open_date"]) if fhsa.get("open_date") else date.today())
                fhsa_carry = st.number_input("Carryforward room", min_value=0.0, value=float(fhsa.get("carryforward_room") or 0), step=100.0)
                fhsa_first_time = st.checkbox("First-time buyer eligible", value=bool(fhsa.get("is_first_time_buyer", 1)))
                fhsa_status = st.selectbox("Closure status", ["open", "closed_withdrawal", "closed_transfer", "expired"], index=["open", "closed_withdrawal", "closed_transfer", "expired"].index(fhsa.get("closure_status") or "open"))

            if st.form_submit_button("Save room snapshots", type="primary"):
                save_tfsa_state(
                    conn,
                    user_id,
                    snapshot_year=tfsa_year,
                    prior_unused_room=tfsa_unused,
                    prior_year_withdrawals=tfsa_withdrawals,
                    ytd_contributions=tfsa_ytd,
                    was_non_resident=tfsa_non_resident,
                    available_room=snapshots["tfsa"].available_room,
                )
                save_rrsp_state(
                    conn,
                    user_id,
                    snapshot_year=rrsp_year,
                    prior_unused_room=rrsp_unused,
                    prior_year_earned_income=rrsp_income,
                    pension_adjustment=rrsp_pa,
                    ytd_contributions=rrsp_ytd,
                    deduction_limit=snapshots["rrsp"].deduction_limit,
                )
                save_fhsa_state(
                    conn,
                    user_id,
                    open_date=fhsa_open,
                    carryforward_room=fhsa_carry,
                    is_first_time_buyer=fhsa_first_time,
                    closure_status=fhsa_status,
                )
                st.success("Room tracker updated.")
                st.rerun()

        st.divider()
        warnings = snapshots["tfsa"].warnings + snapshots["fhsa"].warnings
        for warning in warnings:
            st.warning(warning)
        st.caption("Verify with CRA My Account when possible.")
    finally:
        conn.close()

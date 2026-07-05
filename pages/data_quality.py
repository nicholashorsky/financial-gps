"""Data quality warnings and actionable flags."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from budget.narrator import fire_date_message
from shared.db import get_connection
from shared.fire_service import estimate_fire_date, get_data_quality_warnings


def render() -> None:
    st.title("Data Quality")
    st.caption("This is the page where the model admits what it does not know yet.")

    user = st.session_state.get("user")
    if not user:
        st.info("Log in to review data quality.")
        return

    user_id = int(user["id"])
    conn = get_connection()
    try:
        warnings = get_data_quality_warnings(conn, user_id)
        if not warnings:
            st.success("No major data quality warnings right now.")
            st.caption(fire_date_message(estimate_fire_date(conn, user_id)))
            return

        for warning in warnings:
            if warning.severity == "error":
                st.error(warning.message)
            elif warning.severity == "warning":
                st.warning(warning.message)
            else:
                st.info(warning.message)

        st.divider()
        st.dataframe(
            pd.DataFrame([{"Code": warning.code, "Severity": warning.severity, "Message": warning.message} for warning in warnings]),
            use_container_width=True,
            hide_index=True,
        )
    finally:
        conn.close()

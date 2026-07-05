"""Initial onboarding flow."""

from __future__ import annotations

import streamlit as st

from shared.db import get_connection
from shared.onboarding_service import get_onboarding_status


def render() -> None:
    st.title("Onboarding")
    st.caption("A quick setup pass so the rest of the app has something real to work with.")

    user = st.session_state.get("user")
    if not user:
        st.info("Log in to start onboarding.")
        return

    user_id = int(user["id"])
    conn = get_connection()
    try:
        status = get_onboarding_status(conn, user_id)
        st.progress(status["complete_count"] / len(status["steps"]), text=f"{status['complete_count']} of {len(status['steps'])} setup steps done")

        for step in status["steps"]:
            if step["done"]:
                st.success(step["label"])
            else:
                st.warning(step["label"])

        st.divider()
        import_col, goal_col, fire_col = st.columns(3)
        if import_col.button("Open Spending", use_container_width=True):
            st.session_state.page = "Spending"
            st.rerun()
        if goal_col.button("Open Goals", use_container_width=True):
            st.session_state.page = "Goals"
            st.rerun()
        if fire_col.button("Open FIRE Profile", use_container_width=True):
            st.session_state.page = "Financial Profile"
            st.rerun()

        if status["is_complete"]:
            st.info("The core setup is done. From here, the interesting part is improving the assumptions, not discovering them.")
            if st.button("Go to Home", type="primary", use_container_width=True):
                st.session_state.page = "Home"
                st.rerun()
        elif status["should_prompt_fire"]:
            st.caption("Your transaction history is already helping. The FIRE Planner can now start from defaults instead of blank boxes.")
    finally:
        conn.close()

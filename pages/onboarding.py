"""Initial onboarding flow."""

from __future__ import annotations

import streamlit as st

from shared.db import get_connection
from shared.onboarding_service import get_onboarding_status


STEP_DESTINATIONS = {
    "Import transactions": "Spending",
    "Create a goal": "Goals",
    "Set FIRE profile basics": "Financial Profile",
    "Review FIRE income defaults": "Financial Profile",
}


def _current_step_index(steps: list[dict[str, object]]) -> int:
    saved = int(st.session_state.get("onboarding_step_index", 0))
    if 0 <= saved < len(steps) and not bool(steps[saved]["done"]):
        return saved
    return next((idx for idx, step in enumerate(steps) if not bool(step["done"])), max(len(steps) - 1, 0))


def _set_step(index: int, steps: list[dict[str, object]]) -> None:
    st.session_state.onboarding_step_index = max(0, min(index, len(steps) - 1))
    st.rerun()


def _render_step_list(steps: list[dict[str, object]], current_idx: int) -> None:
    for idx, step in enumerate(steps):
        label = str(step["label"])
        status = "Done" if step["done"] else "Now" if idx == current_idx else "Next"
        with st.container(border=True):
            cols = st.columns([0.18, 0.62, 0.2])
            cols[0].markdown(f"**{idx + 1}**")
            cols[1].write(label)
            cols[2].caption(status)


def _render_current_step(step: dict[str, object], is_complete: bool) -> None:
    label = str(step["label"])
    destination = STEP_DESTINATIONS.get(label, "Home")

    st.subheader(label)
    if label == "Import transactions":
        st.write("Bring in the transaction history first. Everything else gets smarter after the app can see actual cash flow.")
    elif label == "Create a goal":
        st.write("Give the forecast something to aim at: emergency fund, house fund, vacation, retirement, or anything else with a target.")
    elif label == "Set FIRE profile basics":
        st.write("Add province and date of birth so the Canadian FIRE engine can stop guessing about tax and benefit timing.")
    elif label == "Review FIRE income defaults":
        st.write("Check the income that came from your CSV and override anything that does not represent a normal month.")

    if is_complete:
        st.success("This step is complete.")

    if st.button(f"Open {destination}", type="primary", use_container_width=True):
        st.session_state.page = destination
        st.rerun()


def render() -> None:
    st.title("Onboarding")
    st.caption("A guided setup pass so the rest of the app has something real to work with.")

    user = st.session_state.get("user")
    if not user:
        st.info("Log in to start onboarding.")
        return

    user_id = int(user["id"])
    conn = get_connection()
    try:
        status = get_onboarding_status(conn, user_id)
        steps = list(status["steps"])
        current_idx = _current_step_index(steps)
        current_step = steps[current_idx]
        progress = status["complete_count"] / len(steps)

        st.progress(progress, text=f"{status['complete_count']} of {len(steps)} setup steps done")

        left, right = st.columns([0.95, 1.35])
        with left:
            st.subheader("Setup Path")
            _render_step_list(steps, current_idx)
        with right:
            with st.container(border=True):
                st.caption(f"Step {current_idx + 1} of {len(steps)}")
                _render_current_step(current_step, bool(current_step["done"]))

            nav_left, nav_mid, nav_right = st.columns(3)
            if nav_left.button("Previous", use_container_width=True, disabled=current_idx == 0):
                _set_step(current_idx - 1, steps)
            if nav_mid.button("Next", use_container_width=True, disabled=current_idx >= len(steps) - 1):
                _set_step(current_idx + 1, steps)
            if nav_right.button("Skip to Home", use_container_width=True):
                st.session_state.page = "Home"
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

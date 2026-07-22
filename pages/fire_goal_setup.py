"""FIRE variant, target date, and spending floor."""

from __future__ import annotations

from datetime import date

import streamlit as st

from shared.db import get_connection
from shared.fire_service import get_or_create_fire_profile, save_fire_profile
from shared.fire_variants import FIRE_VARIANT_GUIDANCE, FIRE_VARIANTS, fire_variant_label


def _render_variant_comparison() -> None:
    with st.expander("Compare FIRE variants"):
        st.caption("These are planning styles, not recommendations. You can change your choice later.")
        for guidance in FIRE_VARIANT_GUIDANCE.values():
            st.markdown(f"**{guidance['label']}** — {guidance['definition']}")
            st.caption(guidance["impact"])


def render() -> None:
    st.title("FIRE Planner - Goal Setup")
    st.caption("This is where the plan stops being abstract and starts admitting what kind of retirement life you actually mean.")

    user = st.session_state.get("user")
    if not user:
        st.info("Log in to define a FIRE target.")
        return

    user_id = int(user["id"])
    conn = get_connection()
    try:
        profile = get_or_create_fire_profile(conn, user_id)
        with st.form("fire_goal_setup_form"):
            saved_variant = profile.get("fire_variant")
            variant = st.selectbox(
                "FIRE variant",
                FIRE_VARIANTS,
                index=FIRE_VARIANTS.index(saved_variant) if saved_variant in FIRE_VARIANTS else 0,
                format_func=fire_variant_label,
                help="Choose the planning style that best describes your goal. This does not change forecast inputs automatically.",
            )
            selected_guidance = FIRE_VARIANT_GUIDANCE[variant]
            st.info(f"{selected_guidance['definition']} {selected_guidance['impact']}")
            _render_variant_comparison()
            target_year = st.number_input("Target retire year", min_value=date.today().year, max_value=date.today().year + 50, value=int(profile.get("target_retire_year") or date.today().year + 15))
            spending_floor = st.number_input("Annual spending floor", min_value=0.0, value=float(profile.get("spending_floor") or 50000), step=1000.0)
            spending_ceiling = st.number_input("Annual spending ceiling", min_value=0.0, value=float(profile.get("spending_ceiling") or max(spending_floor * 1.3, 65000)), step=1000.0)
            st.caption(
                "The variant is a label for your planning approach. Your target year, spending band, income, "
                "and account balances are the values that drive the forecast."
            )

            if st.form_submit_button("Save FIRE goal", type="primary"):
                save_fire_profile(
                    conn,
                    user_id,
                    fire_variant=variant,
                    target_retire_year=target_year,
                    spending_floor=spending_floor,
                    spending_ceiling=spending_ceiling,
                )
                st.success("FIRE goal saved.")
                st.rerun()

        st.divider()
        years_to_goal = int(target_year - date.today().year)
        st.metric("Years to target", years_to_goal)
        st.caption(f"{fire_variant_label(variant)} with a spending band of ${spending_floor:,.0f} to ${spending_ceiling:,.0f}.")
    finally:
        conn.close()

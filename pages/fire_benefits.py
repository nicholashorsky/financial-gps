"""CPP / OAS / GIS benefits workspace."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from budget.narrator import cpp_delay_message, gis_message
from fire_engine.calculators import estimate_gis
from shared.db import get_connection
from shared.fire_service import benefit_previews, get_or_create_fire_profile, list_benefit_enrollments, upsert_benefit_enrollment


def render() -> None:
    st.title("FIRE Planner - Benefits Workspace")
    st.caption("Benefit elections matter more than they look. This page is where we make those tradeoffs explicit.")

    user = st.session_state.get("user")
    if not user:
        st.info("Log in to manage benefit assumptions.")
        return

    user_id = int(user["id"])
    conn = get_connection()
    try:
        profile = get_or_create_fire_profile(conn, user_id)
        previews = benefit_previews(conn, user_id)
        benefits = {row["benefit_type"]: row for row in list_benefit_enrollments(conn, user_id)}

        with st.form("fire_benefits_form"):
            left, right = st.columns(2)
            with left:
                cpp_age = st.slider("CPP start age", min_value=60, max_value=70, value=int(benefits.get("CPP", {}).get("elected_start_age") or 65))
                cpp_preview = previews["cpp_60"] if cpp_age == 60 else previews["cpp_65"] if cpp_age == 65 else previews["cpp_70"]
                st.metric("CPP monthly preview", f"${cpp_preview.monthly_amount:,.2f}")
                st.caption(f"Delaying CPP changes the lifetime income profile immediately in the engine.")
            with right:
                oas_age = st.slider("OAS start age", min_value=65, max_value=70, value=int(benefits.get("OAS", {}).get("elected_start_age") or 65))
                oas_preview = previews["oas_65"] if oas_age == 65 else previews["oas_70"]
                st.metric("OAS monthly preview", f"${oas_preview.monthly_amount:,.2f}")
                st.caption("Partial pension depends on years resident in Canada.")

            income_guess = float(next((row["annual_amount"] for row in conn.execute("SELECT annual_amount FROM fire_income_sources WHERE user_id = ? ORDER BY id ASC", (user_id,)).fetchall()), 0) or 0)
            gis_preview = estimate_gis(income_guess, income_guess, False)
            st.metric("GIS preview", f"${gis_preview.annual_amount:,.2f}")
            st.caption(gis_message(gis_preview.annual_amount))

            if st.form_submit_button("Save benefit elections", type="primary"):
                upsert_benefit_enrollment(
                    conn,
                    user_id,
                    "CPP",
                    cpp_age,
                    estimated_monthly_amount=cpp_preview.monthly_amount,
                    source="calculated",
                    cpp_estimate_at_65=previews["cpp_65"].monthly_amount,
                )
                upsert_benefit_enrollment(
                    conn,
                    user_id,
                    "OAS",
                    oas_age,
                    estimated_monthly_amount=oas_preview.monthly_amount,
                    source="calculated",
                    oas_years_resident=int(profile.get("years_in_canada_post_18") or 40),
                )
                st.success("Benefits workspace updated.")
                st.rerun()

        st.divider()
        st.info(cpp_delay_message(previews["cpp_65"].monthly_amount, previews["cpp_70"].monthly_amount))
    finally:
        conn.close()

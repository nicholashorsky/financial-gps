"""CPP / OAS / GIS benefits workspace."""

from __future__ import annotations

import streamlit as st

from budget.narrator import cpp_delay_message, gis_message
from fire_engine.calculators import adjust_cpp_for_start_age, estimate_gis
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
        saved_cpp = benefits.get("CPP", {})

        with st.form("fire_benefits_form"):
            left, right = st.columns(2)
            with left:
                saved_cpp_at_65 = saved_cpp.get("cpp_estimate_at_65")
                cpp_estimate_at_65 = st.number_input(
                    "Service Canada monthly CPP estimate at age 65",
                    min_value=0.0,
                    value=float(saved_cpp_at_65 or 0),
                    step=25.0,
                    help=(
                        "Use the monthly age-65 estimate from your My Service Canada Account. "
                        "Leave this at $0 to use Financial GPS's planning estimate."
                    ),
                )
                cpp_age = st.slider(
                    "CPP start age",
                    min_value=60,
                    max_value=70,
                    value=int(saved_cpp.get("elected_start_age") or 65),
                )
                if cpp_estimate_at_65 > 0:
                    cpp_preview = adjust_cpp_for_start_age(cpp_estimate_at_65, cpp_age)
                    cpp_source = "manual"
                    st.caption("Source: your Service Canada age-65 estimate")
                else:
                    cpp_preview = adjust_cpp_for_start_age(previews["cpp_65"].monthly_amount, cpp_age)
                    cpp_source = "calculated"
                    st.caption("Source: Financial GPS planning estimate based on 70% of maximum CPP")
                st.metric(
                    f"Estimated CPP at age {cpp_age}",
                    f"${cpp_preview.monthly_amount:,.0f}/mo",
                )
                st.caption("Your start age is modeled separately from the age-65 amount you enter.")
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
                    source=cpp_source,
                    cpp_estimate_at_65=cpp_estimate_at_65 or previews["cpp_65"].monthly_amount,
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

"""User profile, income, assumptions, and category rule settings."""

from __future__ import annotations

import streamlit as st

from auth import update_user_profile
from budget.categorizer import add_user_rule, delete_user_rule, list_category_rules, seed_system_rules
from shared.db import get_connection
from shared.fire_service import get_or_create_fire_profile, save_fire_profile


def render() -> None:
    st.title("Settings")
    st.caption("Profile details, category rules, and the small places where defaults can go wrong.")

    user = st.session_state.get("user", {})
    if not user:
        st.info("Log in to edit settings.")
        return

    user_id = int(user["id"])
    conn = get_connection()
    try:
        seed_system_rules(conn, user_id)
        fire_profile = get_or_create_fire_profile(conn, user_id)

        profile_col, rules_col = st.columns([1, 1.4])
        with profile_col:
            st.subheader("Profile")
            with st.form("profile_settings_form"):
                st.text(f"Email: {user.get('email', '')}")
                display_name = st.text_input("Name", value=user.get("name") or "")
                variant_options = ["lean", "coast", "barista", "fat"]
                fire_variant = st.selectbox(
                    "Default FIRE variant",
                    variant_options,
                    index=variant_options.index(fire_profile.get("fire_variant")) if fire_profile.get("fire_variant") in variant_options else 1,
                )
                spending_floor = st.number_input(
                    "FIRE spending floor",
                    min_value=0.0,
                    value=float(fire_profile.get("spending_floor") or 45000),
                    step=1000.0,
                )
                spending_ceiling = st.number_input(
                    "FIRE spending ceiling",
                    min_value=0.0,
                    value=float(fire_profile.get("spending_ceiling") or 65000),
                    step=1000.0,
                )
                if st.form_submit_button("Save profile settings", type="primary"):
                    updated_user = update_user_profile(user_id, name=display_name.strip() or None)
                    save_fire_profile(
                        conn,
                        user_id,
                        fire_variant=fire_variant,
                        spending_floor=spending_floor,
                        spending_ceiling=spending_ceiling,
                    )
                    if updated_user:
                        st.session_state.user = updated_user
                    st.success("Profile settings saved.")
                    st.rerun()

        with rules_col:
            st.subheader("Categorization Rules")
            st.caption("User rules are checked before the system defaults.")

            with st.form("add_rule_form", clear_on_submit=True):
                keyword = st.text_input("Keyword")
                category = st.text_input("Category")
                priority = st.slider("Priority", min_value=0, max_value=100, value=50)
                submitted = st.form_submit_button("Add rule", type="primary")
                if submitted:
                    try:
                        add_user_rule(conn, user_id, keyword, category, priority)
                        st.success("Rule added.")
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))

            rules = list_category_rules(conn, user_id)
            if not rules:
                st.info("No rules yet.")
            else:
                for rule_id, keyword, category, priority, source in rules:
                    cols = st.columns([2.2, 1.5, 0.8, 0.8])
                    cols[0].write(keyword)
                    cols[1].write(category)
                    cols[2].write(priority)
                    cols[3].write(source)
                    if source == "user":
                        if cols[3].button("Delete", key=f"delete_rule_{rule_id}"):
                            delete_user_rule(conn, rule_id, user_id)
                            st.rerun()
    finally:
        conn.close()

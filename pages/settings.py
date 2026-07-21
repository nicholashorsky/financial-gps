"""User profile, income, assumptions, and category rule settings."""

from __future__ import annotations

import streamlit as st

from auth import update_user_profile
from budget.categorizer import (
    add_user_category,
    add_user_rule,
    count_rule_matches,
    delete_user_rule,
    get_user_categories,
    list_category_rules,
    list_user_categories,
    rename_user_category,
    seed_system_rules,
    seed_user_categories,
    set_category_enabled,
    set_rule_enabled,
    update_user_rule,
)
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
        seed_user_categories(conn, user_id)
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
            category_options = get_user_categories(conn, user_id)

            with st.form("add_rule_form", clear_on_submit=True):
                keyword = st.text_input("Keyword")
                category = st.selectbox("Category", category_options)
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
                for rule_id, keyword, category, priority, source, enabled in rules:
                    cols = st.columns([2.2, 1.5, 0.8, 0.8, 0.8])
                    cols[0].write(keyword)
                    cols[1].write(category)
                    cols[2].write(priority)
                    cols[3].write(source)
                    if cols[4].button("Disable" if enabled else "Enable", key=f"toggle_rule_{rule_id}"):
                        set_rule_enabled(conn, rule_id, user_id, not enabled)
                        st.rerun()
                    if source == "user":
                        with st.expander(f"Edit rule: {keyword}"):
                            with st.form(f"edit_rule_{rule_id}"):
                                edited_keyword = st.text_input("Keyword", value=keyword)
                                category_index = category_options.index(category) if category in category_options else 0
                                edited_category = st.selectbox("Category", category_options, index=category_index)
                                edited_priority = st.slider("Priority", 0, 100, int(priority))
                                st.caption(
                                    f"Preview: this keyword matches {count_rule_matches(conn, user_id, edited_keyword)} "
                                    "existing transaction(s). Saving the rule will not recategorize them."
                                )
                                edit_actions = st.columns(2)
                                if edit_actions[0].form_submit_button("Save changes", type="primary"):
                                    update_user_rule(
                                        conn,
                                        rule_id,
                                        user_id,
                                        edited_keyword,
                                        edited_category,
                                        edited_priority,
                                    )
                                    st.success("Rule updated. Existing transactions were not changed.")
                                    st.rerun()
                                if edit_actions[1].form_submit_button("Delete rule"):
                                    delete_user_rule(conn, rule_id, user_id)
                                    st.rerun()

            st.divider()
            st.subheader("Categories")
            st.caption("Default categories remain available unless you disable them. Changes apply only to your account.")
            with st.form("add_category_form", clear_on_submit=True):
                new_category = st.text_input("New category")
                if st.form_submit_button("Add category", type="primary"):
                    try:
                        add_user_category(conn, user_id, new_category)
                        st.success("Category added.")
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))

            for category_row in list_user_categories(conn, user_id):
                category_id = int(category_row["id"])
                name = str(category_row["name"])
                enabled = bool(category_row["is_enabled"])
                cols = st.columns([2.5, 1, 1])
                cols[0].write(name)
                cols[1].caption("Default" if category_row["is_default"] else "Custom")
                if cols[2].button("Disable" if enabled else "Enable", key=f"toggle_category_{category_id}"):
                    try:
                        set_category_enabled(conn, user_id, category_id, not enabled)
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))
                if not category_row["is_default"]:
                    with st.expander(f"Rename category: {name}"):
                        with st.form(f"rename_category_{category_id}"):
                            renamed = st.text_input("Category name", value=name)
                            if st.form_submit_button("Rename"):
                                try:
                                    rename_user_category(conn, user_id, category_id, renamed)
                                    st.success("Category renamed.")
                                    st.rerun()
                                except ValueError as exc:
                                    st.error(str(exc))
    finally:
        conn.close()

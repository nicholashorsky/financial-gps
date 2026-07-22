"""User profile, income, assumptions, and category rule settings."""

from __future__ import annotations

import streamlit as st

from auth import delete_user_account, update_user_profile
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
from shared.beta_policy import ACCOUNT_DELETION_NOTICE
from shared.fire_service import get_or_create_fire_profile, save_fire_profile
from shared.fire_variants import FIRE_VARIANTS, fire_variant_label


def _render_profile_settings(user: dict, user_id: int) -> None:
    st.subheader("Profile")
    st.caption("Your account identity and display name.")
    with st.form("profile_settings_form"):
        st.text(f"Email: {user.get('email', '')}")
        display_name = st.text_input("Name", value=user.get("name") or "")
        if st.form_submit_button("Save profile", type="primary"):
            updated_user = update_user_profile(
                user_id,
                name=display_name.strip() or None,
            )
            if updated_user:
                st.session_state.user = updated_user
            st.session_state.settings_notice = "Profile saved."
            st.rerun()


def _render_financial_assumptions(conn, user_id: int, fire_profile: dict) -> None:
    st.subheader("Financial assumptions")
    st.caption("Defaults used by FIRE planning. Detailed profile inputs remain in Financial Profile.")
    with st.form("financial_assumptions_form"):
        saved_variant = fire_profile.get("fire_variant")
        fire_variant = st.selectbox(
            "Default FIRE variant",
            FIRE_VARIANTS,
            index=FIRE_VARIANTS.index(saved_variant) if saved_variant in FIRE_VARIANTS else 1,
            format_func=fire_variant_label,
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
        if st.form_submit_button("Save financial assumptions", type="primary"):
            save_fire_profile(
                conn,
                user_id,
                fire_variant=fire_variant,
                spending_floor=spending_floor,
                spending_ceiling=spending_ceiling,
            )
            st.session_state.settings_notice = "Financial assumptions saved."
            st.rerun()


def _render_rules(conn, user_id: int, category_options: list[str]) -> None:
    st.subheader("Categorization rules")
    with st.container():
        st.caption("User rules are checked before system defaults. Changes apply only to your account.")
        with st.form("add_rule_form", clear_on_submit=True):
            keyword = st.text_input("Keyword")
            category = st.selectbox("Category", category_options)
            priority = st.slider("Priority", min_value=0, max_value=100, value=50)
            if st.form_submit_button("Add rule", type="primary"):
                try:
                    add_user_rule(conn, user_id, keyword, category, priority)
                    st.session_state.settings_notice = "Rule added."
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

        rules = list_category_rules(conn, user_id)
        if not rules:
            st.info("No categorization rules yet. Add a keyword rule above when you need one.")
            return

        for rule_id, keyword, category, priority, source, enabled in rules:
            with st.container(border=True):
                st.markdown(f"**{keyword}** → **{category}**")
                st.caption(
                    f"Priority {priority} · {'System default' if source == 'system' else 'Your rule'} · "
                    f"{'Enabled' if enabled else 'Disabled'}"
                )
                if st.button("Disable" if enabled else "Enable", key=f"toggle_rule_{rule_id}"):
                    set_rule_enabled(conn, rule_id, user_id, not enabled)
                    st.session_state.settings_notice = f"Rule {'enabled' if not enabled else 'disabled'}."
                    st.rerun()
                if source == "user":
                    with st.expander("Edit or delete this rule"):
                        with st.form(f"edit_rule_{rule_id}"):
                            edited_keyword = st.text_input("Keyword", value=keyword)
                            category_index = category_options.index(category) if category in category_options else 0
                            edited_category = st.selectbox("Category", category_options, index=category_index)
                            edited_priority = st.slider("Priority", 0, 100, int(priority))
                            st.caption(
                                f"Preview: this keyword matches {count_rule_matches(conn, user_id, edited_keyword)} "
                                "existing transaction(s). Saving the rule will not recategorize them."
                            )
                            if st.form_submit_button("Save changes", type="primary"):
                                update_user_rule(
                                    conn,
                                    rule_id,
                                    user_id,
                                    edited_keyword,
                                    edited_category,
                                    edited_priority,
                                )
                                st.session_state.settings_notice = (
                                    "Rule updated. Existing transactions were not changed."
                                )
                                st.rerun()
                            if st.form_submit_button("Delete rule"):
                                delete_user_rule(conn, rule_id, user_id)
                                st.session_state.settings_notice = "Rule deleted."
                                st.rerun()


def _render_categories(conn, user_id: int) -> None:
    st.subheader("Categories")
    with st.container():
        st.caption("Default categories remain available unless disabled. Changes apply only to your account.")
        with st.form("add_category_form", clear_on_submit=True):
            new_category = st.text_input("New category")
            if st.form_submit_button("Add category", type="primary"):
                try:
                    add_user_category(conn, user_id, new_category)
                    st.session_state.settings_notice = "Category added."
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

        categories = list_user_categories(conn, user_id)
        if not categories:
            st.info("No categories are configured yet.")
            return

        for category_row in categories:
            category_id = int(category_row["id"])
            name = str(category_row["name"])
            enabled = bool(category_row["is_enabled"])
            with st.container(border=True):
                st.markdown(f"**{name}**")
                st.caption(
                    f"{'Default' if category_row['is_default'] else 'Custom'} · "
                    f"{'Enabled' if enabled else 'Disabled'}"
                )
                if st.button("Disable" if enabled else "Enable", key=f"toggle_category_{category_id}"):
                    try:
                        set_category_enabled(conn, user_id, category_id, not enabled)
                        st.session_state.settings_notice = (
                            f"Category {'enabled' if not enabled else 'disabled'}."
                        )
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))
                if not category_row["is_default"]:
                    with st.expander("Rename this category"):
                        with st.form(f"rename_category_{category_id}"):
                            renamed = st.text_input("Category name", value=name)
                            if st.form_submit_button("Rename"):
                                try:
                                    rename_user_category(conn, user_id, category_id, renamed)
                                    st.session_state.settings_notice = "Category renamed."
                                    st.rerun()
                                except ValueError as exc:
                                    st.error(str(exc))


def _render_account_data(user: dict, user_id: int) -> None:
    st.subheader("Account and data")
    with st.container():
        st.markdown("**Delete beta account**")
        st.warning(ACCOUNT_DELETION_NOTICE)
        with st.form("delete_beta_account_form"):
            confirmation = st.text_input(
                "Type your account email to confirm",
                placeholder=str(user.get("email", "")),
            )
            understood = st.checkbox(
                "I understand that this permanently deletes my beta account and test data."
            )
            delete_submitted = st.form_submit_button(
                "Permanently delete account",
                disabled=not understood,
            )
            if delete_submitted:
                expected_email = str(user.get("email", "")).strip().lower()
                if confirmation.strip().lower() != expected_email:
                    st.error("Enter your account email exactly to confirm deletion.")
                elif delete_user_account(user_id):
                    st.session_state.clear()
                    st.session_state.account_notice = "Your beta account and test data were deleted."
                    st.session_state.page = "Login"
                    st.rerun()
                else:
                    st.error("The account could not be deleted. It may already have been removed.")


def render() -> None:
    st.title("Settings")
    st.caption("Profile details, category rules, and the small places where defaults can go wrong.")

    user = st.session_state.get("user", {})
    if not user:
        st.info("Log in to edit settings.")
        return

    notice = st.session_state.pop("settings_notice", None)
    if notice:
        st.success(notice)

    user_id = int(user["id"])
    conn = get_connection()
    try:
        seed_system_rules(conn, user_id)
        seed_user_categories(conn, user_id)
        fire_profile = get_or_create_fire_profile(conn, user_id)

        category_options = get_user_categories(conn, user_id)
        profile_tab, assumptions_tab, rules_tab, categories_tab, account_tab = st.tabs(
            ["Profile", "Assumptions", "Rules", "Categories", "Account & data"]
        )
        with profile_tab:
            _render_profile_settings(user, user_id)
        with assumptions_tab:
            _render_financial_assumptions(conn, user_id, fire_profile)
        with rules_tab:
            _render_rules(conn, user_id, category_options)
        with categories_tab:
            _render_categories(conn, user_id)
        with account_tab:
            _render_account_data(user, user_id)
    finally:
        conn.close()

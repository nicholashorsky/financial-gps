"""Login page."""

from __future__ import annotations

import os

import streamlit as st

from auth import authenticate_user, get_or_create_test_user
from shared.db import get_connection
from shared.onboarding_service import should_force_onboarding


def _test_login_enabled() -> bool:
    environment = os.getenv("FINANCIAL_GPS_ENV", "development").strip().lower()
    if environment in {"production", "prod"}:
        return False
    if os.getenv("FINANCIAL_GPS_TEST_LOGIN") == "1":
        return True
    try:
        return bool(st.secrets.get("dev", {}).get("allow_test_login", False))
    except Exception:
        return False


def _complete_login(user: dict) -> None:
    st.session_state.authenticated = True
    st.session_state.user = user
    conn = get_connection()
    try:
        st.session_state.page = "Onboarding" if should_force_onboarding(conn, int(user["id"])) else "Home"
    finally:
        conn.close()
    st.rerun()


def render_login() -> None:
    st.subheader("Welcome back")
    st.caption("Future You is waiting for direction.")

    if _test_login_enabled():
        with st.container(border=True):
            st.caption("Development shortcut")
            if st.button("Continue as Beta Tester", type="primary", use_container_width=True):
                _complete_login(get_or_create_test_user())

    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in", type="primary", use_container_width=True)

        if submitted:
            if not email or not password:
                st.error("Email and password are required.")
                return

            user = authenticate_user(email, password)
            if not user:
                st.error("Invalid email or password.")
                return

            _complete_login(user)

    st.divider()
    if st.button("Create an account", use_container_width=True):
        st.session_state.page = "Register"
        st.rerun()

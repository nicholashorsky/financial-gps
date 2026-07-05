"""Login page."""

import streamlit as st

from auth import authenticate_user
from shared.db import get_connection
from shared.onboarding_service import should_force_onboarding


def render_login() -> None:
    st.subheader("Welcome back")
    st.caption("Future You is waiting for direction.")

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

            st.session_state.authenticated = True
            st.session_state.user = user
            conn = get_connection()
            try:
                st.session_state.page = "Onboarding" if should_force_onboarding(conn, int(user["id"])) else "Home"
            finally:
                conn.close()
            st.rerun()

    st.divider()
    if st.button("Create an account", use_container_width=True):
        st.session_state.page = "Register"
        st.rerun()

"""Registration page."""

import streamlit as st

from auth import create_user
from shared.beta_policy import SYNTHETIC_DATA_NOTICE


def render_register() -> None:
    st.subheader("Create your account")
    st.caption("Let's figure out where you're actually headed.")
    st.warning(SYNTHETIC_DATA_NOTICE)

    with st.form("register_form"):
        name = st.text_input("Name (optional)")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm = st.text_input("Confirm password", type="password")
        submitted = st.form_submit_button("Register", type="primary", use_container_width=True)

        if submitted:
            if not email or not password:
                st.error("Email and password are required.")
                return
            if password != confirm:
                st.error("Passwords do not match.")
                return
            if len(password) < 8:
                st.error("Password must be at least 8 characters.")
                return

            user = create_user(email, password, name or None)
            if not user:
                st.error("An account with that email already exists.")
                return

            st.session_state.authenticated = True
            st.session_state.user = {"id": user["id"], "email": user["email"], "name": user.get("name")}
            st.session_state.page = "Onboarding"
            st.success("Account created. Welcome aboard.")
            st.rerun()

    st.divider()
    if st.button("Already have an account? Log in", use_container_width=True):
        st.session_state.page = "Login"
        st.rerun()

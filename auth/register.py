"""Registration page."""

import streamlit as st

from auth import create_user


def render_register() -> None:
    st.subheader("Create your account")
    st.caption("Let's figure out where you're actually headed.")
    st.warning(
        "Synthetic sample data only during this early beta. Do not enter or upload real banking, tax, account, "
        "or other personal financial information. Test data may be reset without notice."
    )

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

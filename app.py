"""Financial GPS — Streamlit entry point."""

from __future__ import annotations

import streamlit as st

from auth.login import render_login
from auth.register import render_register
from pages import (
    data_quality,
    fire_benefits,
    fire_forecast,
    fire_goal_setup,
    fire_profile,
    fire_room_tracker,
    fire_scenarios,
    forecast,
    goals,
    home,
    onboarding,
    scenarios,
    settings,
    spending,
)
from shared.db import get_connection, init_db
from shared.onboarding_service import should_force_onboarding

st.set_page_config(
    page_title="Financial GPS",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

NAV_ITEMS: dict[str, tuple[str, str]] = {
    "Home": ("🏠", "home"),
    "Spending": ("💸", "spending"),
    "Forecast": ("📈", "forecast"),
    "Scenarios": ("🔀", "scenarios"),
    "Goals": ("🎯", "goals"),
}

FIRE_NAV_ITEMS: dict[str, tuple[str, str]] = {
    "Financial Profile": ("👤", "fire_profile"),
    "Account Room Tracker": ("🏦", "fire_room_tracker"),
    "Benefits Workspace": ("📋", "fire_benefits"),
    "FIRE Goal Setup": ("🎯", "fire_goal_setup"),
    "FIRE Forecast": ("📊", "fire_forecast"),
    "FIRE Scenarios": ("🔀", "fire_scenarios"),
    "Data Quality": ("⚠️", "data_quality"),
}

PAGE_RENDERERS = {
    "Onboarding": onboarding.render,
    "Home": home.render,
    "Spending": spending.render,
    "Forecast": forecast.render,
    "Scenarios": scenarios.render,
    "Goals": goals.render,
    "Financial Profile": fire_profile.render,
    "Account Room Tracker": fire_room_tracker.render,
    "Benefits Workspace": fire_benefits.render,
    "FIRE Goal Setup": fire_goal_setup.render,
    "FIRE Forecast": fire_forecast.render,
    "FIRE Scenarios": fire_scenarios.render,
    "Data Quality": data_quality.render,
    "Settings": settings.render,
}


def _init_session() -> None:
    defaults = {
        "authenticated": False,
        "user": None,
        "page": "Home",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _render_sidebar() -> None:
    with st.sidebar:
        st.title("🧭 Financial GPS")
        user = st.session_state.get("user")
        if user:
            st.caption(user.get("name") or user.get("email", ""))

        st.divider()

        for label, (icon, _) in NAV_ITEMS.items():
            if st.button(f"{icon}  {label}", key=f"nav_{label}", use_container_width=True):
                st.session_state.page = label

        st.divider()
        st.markdown("**🔥 FIRE Planner**")

        for label, (icon, _) in FIRE_NAV_ITEMS.items():
            if st.button(f"{icon}  {label}", key=f"nav_fire_{label}", use_container_width=True):
                st.session_state.page = label

        st.divider()
        if st.button("⚙️  Settings", key="nav_settings", use_container_width=True):
            st.session_state.page = "Settings"

        st.divider()
        if st.button("Log out", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user = None
            st.session_state.page = "Login"
            st.rerun()


def main() -> None:
    _init_session()

    if not st.session_state.authenticated:
        page = st.session_state.get("page", "Login")
        if page == "Register":
            render_register()
        else:
            render_login()
        return

    user = st.session_state.get("user")
    if user:
        conn = get_connection()
        try:
            if should_force_onboarding(conn, int(user["id"])) and st.session_state.page not in {"Onboarding", "Spending"}:
                st.session_state.page = "Onboarding"
        finally:
            conn.close()

    _render_sidebar()

    page = st.session_state.page
    renderer = PAGE_RENDERERS.get(page, home.render)
    renderer()


if __name__ == "__main__":
    main()

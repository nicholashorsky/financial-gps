"""Reusable UI compositions built only from supported Streamlit APIs."""

from __future__ import annotations

from collections.abc import Callable

import streamlit as st


def apply_responsive_styles() -> None:
    """Keep Streamlit's native layout readable without wasting phone space."""
    st.markdown(
        """
        <style>
        @media (max-width: 640px) {
            [data-testid="stMainBlockContainer"] {
                padding: 1rem 1rem 2rem;
            }

            [data-testid="stMainBlockContainer"] h1 {
                font-size: 2rem;
                line-height: 1.15;
                margin-bottom: 0.25rem;
            }

            [data-testid="stMainBlockContainer"] h2 {
                font-size: 1.5rem;
                line-height: 1.2;
            }

            [data-testid="stMainBlockContainer"] h3 {
                font-size: 1.2rem;
                line-height: 1.25;
            }

            [data-testid="stHorizontalBlock"] {
                gap: 0.5rem;
            }

            [data-testid="stMetric"] {
                padding: 0.125rem 0;
            }

            [data-testid="stMetricLabel"] {
                font-size: 0.875rem;
                line-height: 1.2;
            }

            [data-testid="stMetricValue"] {
                font-size: 1.75rem;
                line-height: 1.15;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(
    title: str,
    description: str,
    *,
    action_label: str | None = None,
    on_action: Callable[[], None] | None = None,
) -> None:
    if action_label and on_action:
        heading, action = st.columns([4, 1])
        heading.title(title)
        heading.caption(description)
        action.button(action_label, type="primary", width="stretch", on_click=on_action)
        return
    st.title(title)
    st.caption(description)


def empty_state(message: str, *, action_label: str | None = None, on_action: Callable[[], None] | None = None) -> None:
    with st.container(border=True):
        st.info(message)
        if action_label and on_action:
            st.button(action_label, width="stretch", on_click=on_action)

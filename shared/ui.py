"""Reusable UI compositions built only from supported Streamlit APIs."""

from __future__ import annotations

from collections.abc import Callable

import streamlit as st


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

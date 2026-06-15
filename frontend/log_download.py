"""Cached log downloads for Streamlit (API key stays server-side)."""

from __future__ import annotations

import streamlit as st

from api import fetch_run_log, fetch_step_log


@st.cache_data(show_spinner=False, ttl=300)
def cached_run_log_text(clone_run_id: int) -> tuple[str, str]:
    """Return run log body as text plus the suggested filename."""
    data, name = fetch_run_log(clone_run_id)
    return data.decode("utf-8", errors="replace"), name


@st.cache_data(show_spinner=False, ttl=300)
def cached_step_log(clone_run_id: int, clone_function_run_id: int) -> tuple[bytes, str]:
    return fetch_step_log(clone_run_id, clone_function_run_id)

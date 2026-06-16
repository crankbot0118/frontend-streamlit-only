"""Cached log downloads for Streamlit (API key stays server-side)."""

from __future__ import annotations

import streamlit as st

from api import fetch_log_file


@st.cache_data(show_spinner=False, ttl=1)
def cached_log_file_text(location: str) -> tuple[str, str]:
    """Return log body as text for an instance file path plus the suggested filename."""
    data, name = fetch_log_file(location)
    return data.decode("utf-8", errors="replace"), name

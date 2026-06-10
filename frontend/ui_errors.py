"""Streamlit helpers for consistent error display."""

from __future__ import annotations

import streamlit as st

from config.errors import BackendError, ConfigurationError
from config.logging import setup_logging

log = setup_logging("frontend.ui")


def show_error(exc: Exception, *, context: str) -> None:
    """Log an error and show a user-friendly message in the Streamlit UI."""
    if isinstance(exc, BackendError):
        log.warning("%s: %s", context, exc)
        detail = str(exc)
        if exc.status_code is not None:
            detail = f"[HTTP {exc.status_code}] {detail}"
        st.error(f"{context}: {detail}")
        return

    if isinstance(exc, ConfigurationError):
        log.error("Configuration error in %s: %s", context, exc)
        st.error(str(exc))
        return

    log.exception("Unexpected error in %s", context)
    st.error(f"{context}: {exc}")

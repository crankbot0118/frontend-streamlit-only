"""Shared log file viewer popup for run and step logs."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import streamlit as st

from api import get_run, get_run_steps
from config.errors import BackendError
from log_download import cached_log_file_text
from styles import emit_html, log_file_dialog_html, log_file_missing_html

FILE_NOT_FOUND_MESSAGE = "File does not exist, please contact administrator."
_LOG_DIALOG_KEY = "_ca_log_dialog"

FetchFn = Callable[[], tuple[str, str]]


def resolve_log_location(
    *,
    clone_run_id: int,
    clone_function_run_id: int | None = None,
) -> str | None:
    """Resolve a log file path from ``clone_run_status`` or ``clone_function_run_status``.

    When ``clone_function_run_id`` is omitted, returns ``log_location`` for the run.
    When provided, returns ``step_func_log_location`` for that step row.
    """
    if clone_function_run_id is None:
        run = get_run(clone_run_id)
        if not run:
            return None
        location = run.get("log_location")
        return location if location else None

    for step in get_run_steps(clone_run_id):
        if step.get("clone_function_run_id") == clone_function_run_id:
            location = step.get("step_func_log_location")
            return location if location else None
    return None


def _is_file_missing_error(exc: Exception) -> bool:
    if isinstance(exc, BackendError):
        if exc.status_code in (403, 404):
            return True
        detail = str(exc).lower()
        return any(
            phrase in detail
            for phrase in (
                "not found",
                "no log",
                "not available",
                "no step log",
                "not allowed",
            )
        )
    return False


def _resolve_fetch(state: dict[str, Any]) -> FetchFn | None:
    path = (state.get("file_path") or "").strip()
    if not path:
        return None
    return lambda: cached_log_file_text(path)


def render_log_file_body(*, title: str, file_path: str | None, fetch: FetchFn | None) -> None:
    """Render log popup body for an instance log file path."""
    path = (file_path or "").strip()
    if not path or fetch is None:
        emit_html(log_file_missing_html(title, path or None, FILE_NOT_FOUND_MESSAGE))
        return

    try:
        content, filename = fetch()
        emit_html(log_file_dialog_html(title, path, content, filename))
    except Exception as exc:
        if _is_file_missing_error(exc):
            emit_html(log_file_missing_html(title, path, FILE_NOT_FOUND_MESSAGE))
        else:
            emit_html(log_file_missing_html(title, path, f"Could not load log: {exc}"))


@st.dialog(" ", width="large")
def show_log_file_dialog() -> None:
    """Display the shared log viewer popup."""
    state = st.session_state.get(_LOG_DIALOG_KEY) or {}
    render_log_file_body(
        title=state.get("title") or "Log",
        file_path=state.get("file_path"),
        fetch=_resolve_fetch(state),
    )


def open_log_file_dialog(*, title: str, file_path: str | None) -> None:
    """Open the log viewer for an instance log file path."""
    st.session_state[_LOG_DIALOG_KEY] = {
        "title": title,
        "file_path": file_path,
    }
    show_log_file_dialog()


def open_log_dialog(
    *,
    title: str,
    clone_run_id: int,
    clone_function_run_id: int | None = None,
) -> None:
    """Open the shared log viewer for a run or step log.

    View Log: ``clone_function_run_id`` omitted → ``log_location`` from
    ``clone_run_status``.

    View Step Log: ``clone_function_run_id`` set → ``step_func_log_location``
    from ``clone_function_run_status``.
    """
    open_log_file_dialog(
        title=title,
        file_path=resolve_log_location(
            clone_run_id=clone_run_id,
            clone_function_run_id=clone_function_run_id,
        ),
    )

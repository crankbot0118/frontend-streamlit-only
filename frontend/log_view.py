"""Shared log file viewer popup for run and step logs."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import streamlit as st

from api import get_run, get_run_steps
from config.errors import BackendError
from log_download import cached_run_log_text, cached_step_log_text
from styles import emit_html, log_file_dialog_html, log_file_missing_html

FILE_NOT_FOUND_MESSAGE = "File does not exist, please contact administrator."
_LOG_DIALOG_KEY = "_ca_log_dialog"

FetchFn = Callable[[], tuple[str, str]]


def run_log_location(clone_run_id: int) -> str | None:
    """Return ``log_location`` from ``clone_run_status`` for a run."""
    run = get_run(clone_run_id)
    if not run:
        return None
    location = run.get("log_location")
    return location if location else None


def step_func_log_location(clone_run_id: int, clone_function_run_id: int) -> str | None:
    """Return ``step_func_log_location`` from ``clone_function_run_status`` for one step row."""
    for step in get_run_steps(clone_run_id):
        if step.get("clone_function_run_id") == clone_function_run_id:
            location = step.get("step_func_log_location")
            return location if location else None
    return None


def _is_file_missing_error(exc: Exception) -> bool:
    if isinstance(exc, BackendError):
        if exc.status_code == 404:
            return True
        detail = str(exc).lower()
        return any(
            phrase in detail
            for phrase in ("not found", "no log", "not available", "no step log")
        )
    return False


def _resolve_fetch(state: dict[str, Any]) -> FetchFn | None:
    clone_run_id = state.get("clone_run_id")
    if clone_run_id is None:
        return None

    step_id = state.get("clone_function_run_id")
    if step_id is not None:
        return lambda: cached_step_log_text(clone_run_id, step_id)
    return lambda: cached_run_log_text(clone_run_id)


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


def open_log_file_dialog(
    *,
    title: str,
    file_path: str | None,
    clone_run_id: int,
    clone_function_run_id: int | None = None,
) -> None:
    """Open the log viewer for a run or step log file from the target instance.

    ``file_path`` must be ``log_location`` from ``clone_run_status`` (run log) or
    ``step_func_log_location`` from ``clone_function_run_status`` (step log).
    """
    st.session_state[_LOG_DIALOG_KEY] = {
        "title": title,
        "file_path": file_path,
        "clone_run_id": clone_run_id,
        "clone_function_run_id": clone_function_run_id,
    }
    show_log_file_dialog()


def open_run_log_dialog(*, clone_run_id: int, title: str = "Run log") -> None:
    """Open the run log popup using ``log_location`` from ``clone_run_status``."""
    open_log_file_dialog(
        title=title,
        file_path=run_log_location(clone_run_id),
        clone_run_id=clone_run_id,
    )


def open_step_log_dialog(
    *,
    clone_run_id: int,
    clone_function_run_id: int,
    title: str,
) -> None:
    """Open the step log popup using ``step_func_log_location`` for one step row."""
    open_log_file_dialog(
        title=title,
        file_path=step_func_log_location(clone_run_id, clone_function_run_id),
        clone_run_id=clone_run_id,
        clone_function_run_id=clone_function_run_id,
    )

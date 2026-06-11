"""Run History page — lists clone runs as clickable cards with filters."""

from datetime import date

import streamlit as st

from api import get_run_filters, get_runs
from config.settings import frontend
from styles import goto_page, render_run_card, render_title
from ui_errors import show_error

_RUN_HISTORY_LIMIT = min(frontend().max_run_limit, 25)

render_title(
    "Run History",
    subtitle="Review past clone runs and their outcomes.",
)

ALL = "All"


def _parse_date_range(value) -> tuple[date | None, date | None]:
    if not value:
        return None, None
    if isinstance(value, tuple):
        if len(value) >= 2:
            return value[0], value[1]
        if len(value) == 1:
            return value[0], value[0]
    if isinstance(value, date):
        return value, value
    return None, None


try:
    filter_opts = get_run_filters()
except Exception as exc:
    show_error(exc, context="Could not load filter options")
    filter_opts = {"targets": [], "users": []}

with st.container(key="ca-run-filters"):
    c_target, c_user, c_range = st.columns(3)
    with c_target:
        target = st.selectbox(
            "Target",
            options=[ALL, *filter_opts["targets"]],
            key="filter_target",
        )
    with c_user:
        user = st.selectbox(
            "User",
            options=[ALL, *filter_opts["users"]],
            key="filter_user",
        )
    with c_range:
        date_range = st.date_input(
            "Date range",
            value=(),
            format="DD/MM/YYYY",
            key="filter_date_range",
            selection_mode="range",
        )

target_val = None if target == ALL else target
user_val = None if user == ALL else user
start_val, end_val = _parse_date_range(date_range)
filters_active = any([target_val, user_val, start_val, end_val])

try:
    runs = get_runs(
        limit=_RUN_HISTORY_LIMIT,
        target=target_val,
        user=user_val,
        start_date=start_val,
        end_date=end_val,
    )
except Exception as exc:
    show_error(exc, context="Could not load runs")
    runs = []

runs = sorted(
    runs,
    key=lambda r: (r.get("last_update") or "", r.get("clone_run_id") or 0),
    reverse=True,
)

if not runs:
    if filters_active:
        st.info(
            "No runs match your filters. Try a different target, user, or date range."
        )
    else:
        st.caption("No runs to show yet.")
else:
    with st.container(key="ca-runs"):
        for run in runs:
            if render_run_card(run):
                st.session_state["selected_run_id"] = run["clone_run_id"]
                st.session_state["selected_run"] = run
                st.session_state[f"auto_refresh_{run['clone_run_id']}"] = True
                st.session_state["_auto_refresh_run"] = run["clone_run_id"]
                st.query_params["run"] = str(run["clone_run_id"])
                goto_page("Run details")

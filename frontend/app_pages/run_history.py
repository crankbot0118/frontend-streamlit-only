"""Run History page — lists clone runs as clickable cards with filters."""

from datetime import date

import streamlit as st

from api import get_run_filters, get_runs
from styles import goto_page, render_run_card, render_title

render_title(
    "Run History",
    subtitle="Review past clone runs and their outcomes.",
)

ALL = "All"

try:
    filter_opts = get_run_filters()
except Exception:
    st.error("Could not reach the backend to load filter options. Is the API running?")
    filter_opts = {"clients": [], "targets": [], "users": []}

with st.container(key="ca-run-filters"):
    c_client, c_target, c_user, c_date = st.columns(4)
    with c_client:
        client = st.selectbox(
            "Client",
            options=[ALL, *filter_opts["clients"]],
            key="filter_client",
        )
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
    with c_date:
        start_date = st.date_input(
            "Start date",
            value=None,
            format="DD/MM/YYYY",
            key="filter_start_date",
        )

client_val = None if client == ALL else client
target_val = None if target == ALL else target
user_val = None if user == ALL else user
start_val = start_date if isinstance(start_date, date) else None
filters_active = any([client_val, target_val, user_val, start_val])

try:
    runs = get_runs(
        client=client_val,
        target=target_val,
        user=user_val,
        start_date=start_val,
    )
except Exception:
    st.error("Could not reach the backend to load runs. Is the API running?")
    runs = []

runs = sorted(
    runs,
    key=lambda r: (r.get("last_update") or "", r.get("clone_run_id") or 0),
    reverse=True,
)

if not runs:
    if filters_active:
        st.info("No runs match your filters. Try a different client, target, user, or start date.")
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

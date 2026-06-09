"""Run History page — lists all clone runs as clickable cards."""

import streamlit as st

from api import get_runs
from styles import render_run_card, render_title

render_title(
    "Run History",
    subtitle="Review past clone runs and their outcomes.",
)

try:
    runs = get_runs()
except Exception:
    st.error("Could not reach the backend to load runs. Is the API running?")
    runs = []

if not runs:
    st.caption("No runs to show yet.")
else:
    with st.container(key="ca-runs"):
        for run in runs:
            if render_run_card(run):
                st.session_state["selected_run_id"] = run["clone_run_id"]
                st.session_state["selected_run"] = run
                st.switch_page("app_pages/run_details.py")

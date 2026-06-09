"""Run details page — shows the steps (clone_function_run_status) for a run."""

import streamlit as st

from api import get_run_steps
from styles import fmt_dt, render_title, status_badge_html

run_id = st.session_state.get("selected_run_id")
run = st.session_state.get("selected_run")

if st.button(":material/arrow_back: Back to Run History", key="back_to_runs"):
    st.switch_page("app_pages/run_history.py")

if not run_id:
    render_title("Run details")
    st.warning("No run selected. Go back to Run History and pick a run.")
    st.stop()

subtitle = None
if run:
    subtitle = (
        f"{run.get('client_name', '')} &middot; "
        f"{run.get('source_name', '')} \u2192 {run.get('target_name', '')}"
    )
render_title(f"Run #{run_id}", subtitle=subtitle)

if run:
    st.html(
        f'<div style="margin-bottom:0.6rem;">{status_badge_html(run.get("status", ""))}</div>'
    )

try:
    steps = get_run_steps(run_id)
except Exception:
    st.error("Could not reach the backend to load steps. Is the API running?")
    steps = []

if not steps:
    st.caption("No steps found for this run.")
else:
    rows = "".join(
        f"""
        <div class="ca-step">
          <div class="ca-step-name">{s.get('function_name', '—')}</div>
          <div>{status_badge_html(s.get('status', ''))}</div>
          <div class="ca-step-time">Start: {fmt_dt(s.get('start_time'))}</div>
          <div class="ca-step-time">End: {fmt_dt(s.get('end_time'))}</div>
        </div>
        """
        for s in steps
    )
    st.html(f'<div class="ca-steps">{rows}</div>')

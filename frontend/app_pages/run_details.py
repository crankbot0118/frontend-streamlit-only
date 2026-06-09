"""Run details page — shows the steps (clone_function_run_status) for a run."""

import streamlit as st

from api import get_run_steps
from styles import (
    fmt_dt,
    fmt_duration,
    fmt_relative_update,
    fmt_started,
    goto_page,
    render_title,
    status_badge_html,
)

run_id = st.session_state.get("selected_run_id")
run = st.session_state.get("selected_run")

if st.button(":material/arrow_back: Back to Run History", key="back_to_runs"):
    goto_page("Run History")

if not run_id:
    render_title("Run details")
    st.warning("No run selected. Go back to Run History and pick a run.")
    st.stop()

if run:
    src = run.get("source_name", "—")
    tgt = run.get("target_name", "—")
    user = run.get("user_name", "—")
    st.html(
        f"""
        <div class="ca-title">
          <h1>Run #{run_id} <span class="ca-run-sep">&middot;</span> {src}
            <span class="arrow">&#8594;</span> {tgt}</h1>
        </div>
        <div class="ca-detail-head">
          <div class="ca-detail-user">{user}</div>
          <div class="ca-detail-meta">
            <span class="ca-run-metaline">
              <span class="mi mi-start">&#9654;</span> Started {fmt_started(run.get('start_date'))}
            </span>
            <span class="ca-run-metaline">
              <span class="mi mi-upd">&#8635;</span> {fmt_relative_update(run.get('last_update'))}
            </span>
            <span class="ca-run-metaline">
              <span class="mi mi-dur">&#9201;</span> {fmt_duration(run.get('start_date'), run.get('last_update'))}
            </span>
          </div>
          <div class="ca-detail-status">{status_badge_html(run.get('status', ''))}</div>
        </div>
        <hr class="ca-title-rule" />
        """
    )
else:
    render_title(f"Run #{run_id}")

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

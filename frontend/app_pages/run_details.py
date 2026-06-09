"""Run details page — shows the steps (clone_function_run_status) for a run."""

import streamlit as st

from api import get_run, get_run_steps
from styles import (
    fmt_dt,
    fmt_duration,
    fmt_relative_update,
    fmt_started,
    goto_page,
    render_title,
    status_badge_html,
    status_image_html,
)

run_id = st.session_state.get("selected_run_id")

# On a hard refresh Streamlit starts a fresh session and session_state is empty,
# so fall back to the run id carried in the URL query param.
if not run_id:
    qp_run = st.query_params.get("run")
    if qp_run is not None:
        try:
            run_id = int(qp_run)
            st.session_state["selected_run_id"] = run_id
        except (TypeError, ValueError):
            run_id = None

run = st.session_state.get("selected_run")
# Re-fetch the run object when it is missing but we know which run we want.
if run_id and (not run or run.get("clone_run_id") != run_id):
    run = get_run(run_id)
    if run:
        st.session_state["selected_run"] = run

# Keep the URL in sync so subsequent refreshes still work.
if run_id:
    st.query_params["run"] = str(run_id)

if st.button(
    "Back to Run History",
    icon=":material/arrow_back:",
    key="back_to_runs",
):
    st.query_params.clear()
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
    with st.container(key="ca-steps"):
        for i, step in enumerate(steps):
            name = step.get("function_name", "—")
            open_key = f"step_open_{run_id}_{i}"
            is_open = st.session_state.get(open_key, False)
            with st.container(key=f"stepcard_{i}"):
                st.html(
                    f'<div class="ca-step-head">'
                    f'<div class="ca-step-left">'
                    f'<span class="ca-step-name">{name}</span>'
                    f'{status_image_html(step.get("status", ""))}'
                    f"</div>"
                    f'<span class="ca-step-more">More actions</span>'
                    f"</div>"
                )
                arrow = ":material/arrow_drop_down:" if is_open else ":material/arrow_right:"
                if st.button("", key=f"more_{i}", icon=arrow, help="More actions"):
                    st.session_state[open_key] = not is_open
                    st.rerun()
                if is_open:
                    st.html(
                        f'<div class="ca-step-detail">'
                        f'<div class="ca-step-time">Start: {fmt_dt(step.get("start_time"))}</div>'
                        f'<div class="ca-step-time">End: {fmt_dt(step.get("end_time"))}</div>'
                        f"</div>"
                    )

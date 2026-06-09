"""Run details page — shows the steps (clone_function_run_status) for a run."""

import time

import streamlit as st

from api import abort_run, get_run, get_run_steps, run_log_url, skip_run
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
# Guard against backend errors so the page degrades instead of crashing.
if run_id and (not run or run.get("clone_run_id") != run_id):
    try:
        run = get_run(run_id)
    except Exception:
        run = None
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

try:
    steps = get_run_steps(run_id)
except Exception:
    st.error("Could not reach the backend to load steps. Is the API running?")
    steps = []

failed_steps = [
    s for s in steps if (s.get("status") or "").upper() == "FAILED"
]
failed_step_id = (
    max(failed_steps, key=lambda s: s["clone_function_run_id"])["clone_function_run_id"]
    if failed_steps
    else None
)

if run:
    src = run.get("source_name", "—")
    tgt = run.get("target_name", "—")
    user = run.get("user_name", "—")
    is_failed = (run.get("status") or "").upper() == "FAILED"
    log_link_html = (
        '<span class="ca-log-sep">&middot;</span>'
        f'<a class="ca-loglink" href="{run_log_url(run_id)}" '
        'target="_blank" rel="noopener" download>View Log</a>'
    )

    with st.container(key="ca-detail-header"):
        with st.container(key="ca-detail-title-row"):
            st.html(
                f"""
                <div class="ca-title ca-detail-title">
                  <h1 class="ca-detail-title-parts">
                    <span>Run #{run_id}</span>
                    <span class="ca-run-sep">&middot;</span>
                    <span>{src}</span>
                    <span class="arrow">&#8594;</span>
                    <span>{tgt}</span>
                  </h1>
                </div>
                """
            )
            with st.container(key="detail-actions"):
                if st.button(
                    "Abort",
                    key="detail_abort",
                    disabled=not is_failed,
                    help="Mark this failed run as ABORTED",
                ):
                    try:
                        abort_run(run_id, failed_step_id)
                        st.session_state.pop("selected_run", None)
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Could not abort run: {exc}")
                if st.button(
                    "Skip",
                    key="detail_skip",
                    disabled=not is_failed,
                    help="Mark this failed run as SKIPPED",
                ):
                    try:
                        skip_run(run_id, failed_step_id)
                        st.session_state.pop("selected_run", None)
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Could not skip run: {exc}")

        meta_col, refresh_col = st.columns([8, 2], vertical_alignment="center")
        with meta_col:
            st.html(
                f"""
                <div class="ca-detail-head">
                  <div class="ca-detail-meta">
                    <span class="ca-run-metaline">Triggered by <span class="ca-trigger-user">{user}</span></span>
                    <span class="ca-detail-sep">&middot;</span>
                    <span class="ca-run-metaline"><span class="mi mi-start">&#9654;</span> Started {fmt_started(run.get('start_date'))}</span>
                    <span class="ca-detail-sep">&middot;</span>
                    <span class="ca-run-metaline"><span class="mi mi-upd">&#8635;</span> {fmt_relative_update(run.get('last_update'))}</span>
                    <span class="ca-detail-sep">&middot;</span>
                    <span class="ca-run-metaline"><span class="mi mi-dur">&#9201;</span> {fmt_duration(run.get('start_date'), run.get('last_update'))}</span>
                    <span class="ca-detail-sep">&middot;</span>
                    {status_badge_html(run.get('status', ''))}{log_link_html}
                  </div>
                </div>
                """
            )
        with refresh_col:
            with st.container(key="detail-refresh"):
                st.toggle("Auto refresh", key=f"auto_refresh_{run_id}")

        st.html('<hr class="ca-title-rule" />')
else:
    render_title(f"Run #{run_id}")

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
                    f'{status_image_html(step.get("status", ""))}'
                    f'<span class="ca-step-name">{name}</span>'
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

if st.session_state.get(f"auto_refresh_{run_id}"):
    st.session_state.pop("selected_run", None)
    time.sleep(3)
    st.rerun()

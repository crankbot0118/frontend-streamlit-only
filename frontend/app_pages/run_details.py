"""Run details page — shows the steps (clone_function_run_status) for a run."""

import html
import sys
from pathlib import Path

import streamlit as st

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from api import (
    abort_run,
    get_run,
    get_run_steps,
    get_step_detail,
    run_log_url,
    skip_run,
    step_log_url,
)
from config.settings import frontend
from styles import (
    fmt_duration,
    fmt_relative_update,
    fmt_started,
    goto_page,
    render_title,
    status_badge_html,
    status_image_html,
    step_action_link_html,
    step_detail_dialog_error_html,
    step_detail_dialog_html,
    _esc,
)

_RUN_DETAILS_REFRESH_SEC = frontend().run_details_refresh_sec


def _toggle_step(open_key: str) -> None:
    st.session_state[open_key] = not st.session_state.get(open_key, False)

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
    if st.session_state.get("_auto_refresh_run") != run_id:
        st.session_state[f"auto_refresh_{run_id}"] = True
        st.session_state["_auto_refresh_run"] = run_id

refresh_key = f"auto_refresh_{run_id}"

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
    src = _esc(run.get("source_name", "—"))
    tgt = _esc(run.get("target_name", "—"))
    user = _esc(run.get("user_name", "—"))
    safe_run_id = _esc(run_id)
    is_failed = (run.get("status") or "").upper() == "FAILED"
    log_href = html.escape(run_log_url(run_id), quote=True)
    log_link_html = (
        '<span class="ca-log-sep">&middot;</span>'
        f'<a class="ca-loglink" href="{log_href}" download>Download Log</a>'
    )

    with st.container(key="ca-detail-header"):
        with st.container(key="ca-detail-title-row"):
            st.html(
                f"""
                <div class="ca-title ca-detail-title">
                  <h1 class="ca-detail-title-parts">
                    <span>Run #{safe_run_id}</span>
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

        with st.container(key="ca-detail-meta-row"):
            st.html(
                f"""
                <div class="ca-detail-meta-bar">
                  <div class="ca-detail-meta">
                    <span class="ca-run-metaline">Triggered by <span class="ca-trigger-user">{user}</span></span>
                    <span class="ca-detail-sep">&middot;</span>
                    <span class="ca-run-metaline"><span class="mi mi-start">&#9654;</span> Started {fmt_started(run.get('start_date'))}</span>
                    <span class="ca-detail-sep">&middot;</span>
                    <span class="ca-run-metaline"><span class="mi mi-upd">&#8635;</span> {fmt_relative_update(run.get('last_update'))}</span>
                    <span class="ca-detail-sep">&middot;</span>
                    <span class="ca-run-metaline"><span class="mi mi-dur">&#9201;</span> {fmt_duration(run.get('start_date'), run.get('last_update'))}</span>
                    <span class="ca-detail-sep">&middot;</span>
                    {status_badge_html(run.get('status', ''))}
                    {log_link_html}
                  </div>
                </div>
                """
            )
            with st.container(key="detail-refresh"):
                st.toggle(
                    "Auto refresh",
                    key=refresh_key,
                    label_visibility="visible",
                )

        st.html('<hr class="ca-title-rule" />')
else:
    render_title(f"Run #{run_id}")

if not steps:
    st.caption("No steps found for this run.")
else:

    @st.dialog(" ", width="large")
    def _show_step_detail_dialog(
        clone_run_id: int,
        clone_function_run_id: int,
        function_name: str,
    ) -> None:
        try:
            detail = get_step_detail(clone_run_id, clone_function_run_id)
        except Exception as exc:
            st.html(step_detail_dialog_error_html(f"Could not load step details: {exc}"))
            return

        if not detail:
            st.html(step_detail_dialog_error_html("No details found for this step."))
            return

        st.html(step_detail_dialog_html(detail, function_name))

    def _render_step_cards(step_rows: list[dict]) -> None:
        for i, step in enumerate(step_rows):
            name = step.get("function_name", "—")
            safe_name = _esc(name)
            step_pk = step.get("clone_function_run_id")
            open_key = f"step_open_{run_id}_{i}"
            is_open = st.session_state.get(open_key, False)
            head_class = "ca-step-head ca-step-head--open" if is_open else "ca-step-head"
            with st.container(key=f"stepcard_{i}"):
                st.html(
                    f'<div class="{head_class}">'
                    f'<div class="ca-step-left">'
                    f'{status_image_html(step.get("status", ""))}'
                    f'<span class="ca-step-name">{safe_name}</span>'
                    f"</div>"
                    f'<span class="ca-step-more">More actions</span>'
                    f"</div>"
                )
                st.button(
                    "",
                    key=f"more_{run_id}_{i}",
                    icon=":material/arrow_right:",
                    help="More actions",
                    on_click=_toggle_step,
                    args=(open_key,),
                )
                if is_open:
                    with st.container(key=f"step_links_{i}"):
                        if st.button("Details", key=f"step_details_{run_id}_{i}"):
                            _show_step_detail_dialog(run_id, step_pk, name)
                        st.html(
                            step_action_link_html(
                                step_log_url(run_id, step_pk)
                                if step.get("step_func_log_location")
                                else None,
                            )
                        )

    def _render_live_steps() -> None:
        st.session_state.pop("selected_run", None)
        live_steps = get_run_steps(run_id)
        _render_step_cards(live_steps)

    with st.container(key="ca-steps"):
        if st.session_state.get(refresh_key):

            @st.fragment(run_every=_RUN_DETAILS_REFRESH_SEC)
            def _auto_refresh_steps() -> None:
                _render_live_steps()

            _auto_refresh_steps()
        else:
            _render_step_cards(steps)

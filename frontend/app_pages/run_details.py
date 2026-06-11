"""Run details page — shows the steps (clone_function_run_status) for a run."""

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
)
from config.settings import frontend
from log_download import cached_run_log, cached_step_log
from styles import (
    emit_html,
    fmt_duration,
    relative_update_html,
    render_title,
    started_html,
    status_badge_html,
    status_image_html,
    step_detail_dialog_error_html,
    step_detail_dialog_html,
    clear_run_details_state,
    goto_page,
    _esc,
)
from ui_errors import show_error

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
    except Exception as exc:
        show_error(exc, context=f"Could not load run #{run_id}")
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

if not run_id:
    render_title("Run details")
    st.warning("No run selected. Go back to Run History and pick a run.")
    st.stop()

try:
    steps = get_run_steps(run_id)
except Exception as exc:
    show_error(exc, context="Could not load run steps")
    steps = []

failed_steps = [
    s for s in steps if (s.get("status") or "").upper() == "FAILED"
]
failed_step_id = (
    max(failed_steps, key=lambda s: s["clone_function_run_id"])["clone_function_run_id"]
    if failed_steps
    else None
)

# Always use latest clone_run_status for operator actions (session run can be stale).
latest_run = run
if run_id:
    try:
        latest_run = get_run(run_id)
        if latest_run:
            st.session_state["selected_run"] = latest_run
    except Exception:
        latest_run = run

run_status = (latest_run.get("status") or "").upper() if latest_run else ""
can_abort_skip = run_status == "FAILED" and failed_step_id is not None

if can_abort_skip:
    _abort_help = "Mark this failed run as ABORTED"
elif run_status != "FAILED":
    _abort_help = "Only available when clone run status is FAILED"
else:
    _abort_help = "No failed function step found for this run"

if run:
    src = _esc(run.get("source_name", "—"))
    tgt = _esc(run.get("target_name", "—"))
    user = _esc(run.get("user_name", "—"))
    safe_run_id = _esc(run_id)
    has_run_log = bool(latest_run.get("log_location"))

    with st.container(key="ca-detail-header"):
        with st.container(key="ca-detail-title-row"):
            st.html(
                f"""
                <div class="ca-page-header ca-detail-page-header">
                  <div class="ca-title">
                    <h1 class="ca-detail-title-parts">
                      <span>Run #{safe_run_id}</span>
                      <span class="ca-run-sep">&middot;</span>
                      <span>{src}</span>
                      <span class="arrow">&#8594;</span>
                      <span>{tgt}</span>
                      <span class="ca-run-sep">&middot;</span>
                    </h1>
                  </div>
                </div>
                """
            )
            with st.container(key="detail-actions"):
                if st.button(
                    "Abort",
                    key="detail_abort",
                    type="secondary",
                    icon=":material/stop:",
                    disabled=not can_abort_skip,
                    help=_abort_help,
                ):
                    if not can_abort_skip:
                        show_error(
                            "Abort is only allowed when clone run status is FAILED.",
                            context="Cannot abort run",
                        )
                    else:
                        try:
                            abort_run(run_id, failed_step_id)
                            st.session_state.pop("selected_run", None)
                            st.rerun()
                        except Exception as exc:
                            show_error(exc, context="Could not abort run")
                if st.button(
                    "",
                    key="detail_close",
                    icon=":material/tab_close:",
                    help="Back to Run History",
                    type="tertiary",
                ):
                    clear_run_details_state()
                    goto_page("Run History")

        with st.container(key="ca-detail-meta-row"):
            col_meta, col_dl, col_ref = st.columns(
                [6, 1, 1.35],
                gap="small",
                vertical_alignment="center",
            )
            with col_meta:
                emit_html(
                    f"""
                    <div class="ca-detail-meta-bar">
                      <div class="ca-detail-meta">
                        <span class="ca-run-metaline">Triggered by <span class="ca-trigger-user">{user}</span></span>
                        <span class="ca-detail-sep">&middot;</span>
                        <span class="ca-run-metaline"><span class="mi mi-start">&#9654;</span> Started {started_html(latest_run.get('start_date'))}</span>
                        <span class="ca-detail-sep">&middot;</span>
                        <span class="ca-run-metaline"><span class="mi mi-upd">&#8635;</span> {relative_update_html(latest_run.get('last_update'))}</span>
                        <span class="ca-detail-sep">&middot;</span>
                        <span class="ca-run-metaline"><span class="mi mi-dur">&#9201;</span> {fmt_duration(latest_run.get('start_date'), latest_run.get('last_update'))}</span>
                        <span class="ca-detail-sep">&middot;</span>
                        {status_badge_html(latest_run.get('status', ''))}
                      </div>
                    </div>
                    """
                )
            with col_dl:
                with st.container(key="detail-download-log"):
                    if has_run_log:
                        try:
                            log_bytes, log_name = cached_run_log(run_id)
                            st.download_button(
                                "View Log",
                                data=log_bytes,
                                file_name=log_name,
                                key=f"download_run_log_{run_id}",
                                type="secondary",
                            )
                        except Exception as exc:
                            show_error(exc, context="Could not load run log")
                    else:
                        st.markdown(
                            '<span class="ca-step-link-disabled">View Log</span>',
                            unsafe_allow_html=True,
                        )
            with col_ref:
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
            emit_html(step_detail_dialog_error_html(f"Could not load step details: {exc}"))
            return

        if not detail:
            emit_html(step_detail_dialog_error_html("No details found for this step."))
            return

        emit_html(step_detail_dialog_html(detail, function_name))

    def _render_step_cards(step_rows: list[dict]) -> None:
        for i, step in enumerate(step_rows):
            name = step.get("function_name", "—")
            safe_name = _esc(name)
            step_pk = step.get("clone_function_run_id")
            open_key = f"step_open_{run_id}_{i}"
            is_open = st.session_state.get(open_key, False)
            with st.container(key=f"stepcard_{i}"):
                left_col, more_col, arrow_col = st.columns(
                    [1, 0.11, 0.04],
                    gap="small",
                    vertical_alignment="center",
                )
                with left_col:
                    st.html(
                        f'<div class="ca-step-left" '
                        f'style="display:flex;align-items:center;gap:8px;flex:1;min-width:0;width:100%;">'
                        f'{status_image_html(step.get("status", ""), size=18)}'
                        f'<span class="ca-step-name" '
                        f'style="font-size:14px;font-weight:600;line-height:1.25;">'
                        f"{safe_name}</span>"
                        f"</div>"
                    )
                with more_col:
                    st.html('<span class="ca-step-more">More actions</span>')
                with arrow_col:
                    st.button(
                        "",
                        key=f"more_{run_id}_{i}",
                        icon=":material/arrow_right:",
                        type="tertiary",
                        on_click=_toggle_step,
                        args=(open_key,),
                    )
                if is_open:
                    with st.container(key=f"step_links_{i}"):
                        if st.button("Details", key=f"step_details_{run_id}_{i}"):
                            _show_step_detail_dialog(run_id, step_pk, name)
                        if step.get("step_func_log_location"):
                            try:
                                step_bytes, step_name = cached_step_log(
                                    run_id, step_pk
                                )
                                st.download_button(
                                    "View Step Log",
                                    data=step_bytes,
                                    file_name=step_name,
                                    key=f"download_step_log_{run_id}_{i}",
                                    type="secondary",
                                )
                            except Exception as exc:
                                show_error(
                                    exc,
                                    context=f"Could not load log for {name}",
                                )
                        else:
                            st.markdown(
                                '<span class="ca-step-link-disabled">'
                                "View Step Log</span>",
                                unsafe_allow_html=True,
                            )

    with st.container(key="ca-steps"):
        auto_on = bool(st.session_state.get(refresh_key))
        poll_every = _RUN_DETAILS_REFRESH_SEC if auto_on else None

        @st.fragment(run_every=poll_every)
        def _steps_panel() -> None:
            if auto_on:
                st.session_state.pop("selected_run", None)
                panel_steps = get_run_steps(run_id)
            else:
                panel_steps = steps
            _render_step_cards(panel_steps)

        _steps_panel()

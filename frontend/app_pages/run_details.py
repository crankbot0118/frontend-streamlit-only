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
    retry_run,
    skip_run,
)
from config.settings import frontend
from log_view import open_run_log_dialog, open_step_log_dialog
from styles import (
    emit_html,
    render_title,
    run_detail_info_dialog_html,
    status_image_html,
    step_detail_dialog_error_html,
    step_detail_dialog_html,
    _esc,
)
from ui_errors import show_error

_RUN_DETAILS_REFRESH_SEC = frontend().run_details_refresh_sec


def _toggle_step(open_key: str) -> None:
    st.session_state[open_key] = not st.session_state.get(open_key, False)


def _load_run(run_id: int, fallback: dict | None = None) -> dict | None:
    try:
        latest = get_run(run_id)
        if latest:
            st.session_state["selected_run"] = latest
            return latest
    except Exception:
        pass
    return fallback


def _load_steps(run_id: int, fallback: list | None = None) -> list:
    try:
        return get_run_steps(run_id)
    except Exception as exc:
        show_error(exc, context="Could not load run steps")
        return fallback or []


def _abort_state(step_rows: list, live_run: dict | None) -> tuple[bool, int | None, str]:
    failed_steps = [
        s for s in step_rows if (s.get("status") or "").upper() == "FAILED"
    ]
    failed_step_id = (
        max(failed_steps, key=lambda s: s["clone_function_run_id"])["clone_function_run_id"]
        if failed_steps
        else None
    )
    run_status = (live_run.get("status") or "").upper() if live_run else ""
    can_abort = run_status == "FAILED" and failed_step_id is not None
    if can_abort:
        help_text = "Mark this failed run as ABORTED"
    elif run_status != "FAILED":
        help_text = "Only available when clone run status is FAILED"
    else:
        help_text = "No failed function step found for this run"
    return can_abort, failed_step_id, help_text


def _step_action_state(step: dict, live_run: dict | None) -> tuple[bool, str]:
    run_status = (live_run.get("status") or "").upper() if live_run else ""
    step_status = (step.get("status") or "").upper()
    enabled = run_status == "FAILED" and step_status == "FAILED"
    if enabled:
        return True, "Act on this failed step"
    if run_status != "FAILED":
        return False, "Only available when clone run status is FAILED"
    if step_status != "FAILED":
        return False, "Only available when this step is FAILED"
    return False, ""

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

steps = _load_steps(run_id)

if run:
    src = _esc(run.get("source_name", "—"))
    tgt = _esc(run.get("target_name", "—"))
    safe_run_id = _esc(run_id)

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

    @st.dialog(" ", width="large")
    def _show_run_info_dialog(clone_run_id: int) -> None:
        try:
            live = get_run(clone_run_id)
        except Exception as exc:
            emit_html(step_detail_dialog_error_html(f"Could not load run info: {exc}"))
            return
        if not live:
            emit_html(step_detail_dialog_error_html("Run not found."))
            return
        emit_html(
            run_detail_info_dialog_html(
                user=_esc(live.get("user_name", "—")),
                start_date=live.get("start_date"),
                last_update=live.get("last_update"),
                status=live.get("status", ""),
            )
        )

    def _render_step_cards(step_rows: list[dict], live_run: dict | None) -> None:
        for i, step in enumerate(step_rows):
            name = step.get("function_name", "—")
            safe_name = _esc(name)
            step_pk = step.get("clone_function_run_id")
            open_key = f"step_open_{run_id}_{i}"
            is_open = st.session_state.get(open_key, False)
            can_act, act_help = _step_action_state(step, live_run)
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
                        st.markdown(
                            '<span class="ca-step-link-sep">&middot;</span>',
                            unsafe_allow_html=True,
                        )
                        if st.button("View Step Log", key=f"view_step_log_{run_id}_{i}"):
                            open_step_log_dialog(
                                clone_run_id=run_id,
                                clone_function_run_id=step_pk,
                                title=f"Step log · {name}",
                            )
                        st.markdown(
                            '<span class="ca-step-link-sep">&middot;</span>',
                            unsafe_allow_html=True,
                        )
                        if st.button(
                            "Retry",
                            key=f"step_retry_{run_id}_{i}",
                            disabled=not can_act,
                            help=act_help,
                        ):
                            try:
                                retry_run(run_id, step_pk)
                                st.session_state.pop("selected_run", None)
                                st.rerun()
                            except Exception as exc:
                                show_error(exc, context="Could not retry step")
                        st.markdown(
                            '<span class="ca-step-link-sep">&middot;</span>',
                            unsafe_allow_html=True,
                        )
                        if st.button(
                            "Skip",
                            key=f"step_skip_{run_id}_{i}",
                            disabled=not can_act,
                            help=act_help,
                        ):
                            try:
                                skip_run(run_id, step_pk)
                                st.session_state.pop("selected_run", None)
                                st.rerun()
                            except Exception as exc:
                                show_error(exc, context="Could not skip step")

    auto_on = bool(st.session_state.get(refresh_key))
    poll_every = _RUN_DETAILS_REFRESH_SEC if auto_on else None

    with st.container(key="ca-detail-header"):
        @st.fragment(run_every=poll_every)
        def _live_detail_panel() -> None:
            polling = bool(st.session_state.get(refresh_key))
            live_run = _load_run(run_id, run) if polling else run
            if not live_run:
                live_run = run
            live_steps = _load_steps(run_id, steps) if polling else steps
            can_abort, failed_step_id, abort_help = _abort_state(live_steps, live_run)

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
                        disabled=not can_abort,
                        help=abort_help,
                    ):
                        if not can_abort:
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
                    st.markdown(
                        '<span class="ca-run-sep ca-detail-action-sep">&middot;</span>',
                        unsafe_allow_html=True,
                    )
                    with st.container(key="detail-info"):
                        if st.button(
                            "Info",
                            key="detail_info",
                            type="secondary",
                            icon=":material/info:",
                            help="Run status and timing",
                        ):
                            _show_run_info_dialog(run_id)

            with st.container(key="ca-detail-meta-row"):
                with st.container(key="detail-meta-actions"):
                    col_dl, col_ref = st.columns(
                        [1, 1.15],
                        gap="small",
                        vertical_alignment="center",
                    )
                    with col_dl:
                        with st.container(key="detail-download-log"):
                            if st.button(
                                "View Log",
                                key=f"view_run_log_{run_id}",
                                type="secondary",
                            ):
                                open_run_log_dialog(clone_run_id=run_id)
                    with col_ref:
                        with st.container(key="detail-refresh"):
                            st.toggle(
                                "Auto refresh",
                                key=refresh_key,
                                label_visibility="visible",
                            )

            st.html('<hr class="ca-title-rule" />')

            if live_steps:
                with st.container(key="ca-steps"):
                    _render_step_cards(live_steps, live_run)
            else:
                st.caption("No steps found for this run.")

        _live_detail_panel()
else:
    render_title(f"Run #{run_id}")
    if not steps:
        st.caption("No steps found for this run.")

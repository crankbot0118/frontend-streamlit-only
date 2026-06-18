"""Run details page — shows the steps (clone_function_run_status) for a run."""

import sys
from pathlib import Path

import streamlit as st

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from api import (
    get_run,
    get_run_steps,
    get_step_detail,
    retry_run,
    skip_run,
)
from config.settings import frontend
from log_view import open_log_dialog
from styles import (
    emit_html,
    render_title,
    run_detail_title_html,
    status_image_html,
    step_detail_dialog_error_html,
    step_detail_dialog_html,
    _esc,
)
from ui_errors import show_error

_RUN_DETAILS_REFRESH_SEC = frontend().run_details_refresh_sec
_TERMINAL_STATUSES = frozenset({"COMPLETED", "FAILED", "ABORTED", "SKIPPED"})
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


def _poll_interval(status: str) -> int | None:
    if (status or "").upper() in _TERMINAL_STATUSES:
        return None
    return _RUN_DETAILS_REFRESH_SEC


def _maybe_rerun_on_terminal(run_id: int, status: str) -> None:
    """Full rerun once when a run reaches a terminal status so polling stops."""
    key = f"_run_status_{run_id}"
    prev = st.session_state.get(key)
    st.session_state[key] = status
    if prev and prev != status and (status or "").upper() in _TERMINAL_STATUSES:
        st.rerun()


def _load_steps(run_id: int, fallback: list | None = None) -> list:
    try:
        return get_run_steps(run_id)
    except Exception as exc:
        show_error(exc, context="Could not load run steps")
        return fallback or []


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
                            open_log_dialog(
                                title=f"Step log · {name}",
                                clone_run_id=run_id,
                                clone_function_run_id=step_pk,
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

    poll_every = _poll_interval(run.get("status", ""))

    with st.container(key="ca-steps"):
        @st.fragment(run_every=poll_every)
        def _live_header() -> None:
            live_run = _load_run(run_id, run) if poll_every else run
            if not live_run:
                live_run = run
            status = live_run.get("status", "")
            if poll_every:
                _maybe_rerun_on_terminal(run_id, status)
            with st.container(key="ca-detail-title-row"):
                st.html(
                    run_detail_title_html(
                        run_id=safe_run_id,
                        src=src,
                        tgt=tgt,
                        status=status,
                    )
                )

        _live_header()

        with st.container(key="ca-detail-log-row"):
            if st.button(
                "View Log",
                key=f"view_run_log_{run_id}",
                type="tertiary",
            ):
                open_log_dialog(
                    title=f"Run log · #{run_id}",
                    clone_run_id=run_id,
                )

        st.html('<hr class="ca-title-rule" />')

        @st.fragment(run_every=poll_every)
        def _live_steps() -> None:
            live_run = _load_run(run_id, run) if poll_every else run
            if not live_run:
                live_run = run
            live_steps = _load_steps(run_id, steps) if poll_every else steps
            if live_steps:
                _render_step_cards(live_steps, live_run)
            else:
                st.caption("No steps found for this run.")

        _live_steps()
else:
    render_title(f"Run #{run_id}")
    if not steps:
        st.caption("No steps found for this run.")

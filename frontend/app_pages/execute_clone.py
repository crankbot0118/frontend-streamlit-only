"""Execute Clone page — trigger a new clone run."""

import sys
from pathlib import Path

import streamlit as st

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from api import get_execute_clone_options, get_run, trigger_clone_run
from config.settings import frontend, is_protected_target_env
from styles import goto_page, render_title

_cfg = frontend()
_PROTECTED_TARGET = _cfg.protected_target_env_name

render_title(
    "Execute Clone",
    subtitle="Select user, source, and target, then trigger a clone job.",
)

PLACEHOLDER = "Select…"


def _is_protected_target(name: str) -> bool:
    return is_protected_target_env(name, _PROTECTED_TARGET)


try:
    options = get_execute_clone_options()
except Exception:
    st.error("Could not reach the backend to load options. Is the API running?")
    st.stop()

users = options.get("users") or []
envs = options.get("environments") or []

if not users:
    st.warning("No users configured yet.")
    st.stop()

if not envs:
    st.warning("No environments configured yet.")
    st.stop()

with st.container(key="ca-execute-clone-form"):
    c_user, c_source, c_target = st.columns(3)

    with c_user:
        user_name = st.selectbox(
            "User",
            options=[PLACEHOLDER, *[u["user_name"] for u in users]],
            key="exec_user",
        )

    selected_user = next((u for u in users if u["user_name"] == user_name), None)
    client_envs = (
        [e for e in envs if e["client_id"] == selected_user["client_id"]]
        if selected_user
        else []
    )

    source_options = [PLACEHOLDER, *[e["env_name"] for e in client_envs]]

    with c_source:
        source_name = st.selectbox(
            "Source",
            options=source_options,
            key="exec_source",
            disabled=selected_user is None,
        )

    target_candidates = [
        e
        for e in client_envs
        if not _is_protected_target(e["env_name"])
        and (source_name == PLACEHOLDER or e["env_name"] != source_name)
    ]
    target_options = [PLACEHOLDER, *[e["env_name"] for e in target_candidates]]

    if st.session_state.get("exec_target") not in target_options:
        st.session_state["exec_target"] = PLACEHOLDER

    with c_target:
        target_name = st.selectbox(
            "Target",
            options=target_options,
            key="exec_target",
            disabled=selected_user is None,
        )

selected_source = next(
    (e for e in client_envs if e["env_name"] == source_name),
    None,
)
selected_target = next(
    (e for e in client_envs if e["env_name"] == target_name),
    None,
)

validation_msgs: list[str] = []
if user_name == PLACEHOLDER:
    validation_msgs.append("Select a user.")
if source_name == PLACEHOLDER:
    validation_msgs.append("Select a source environment.")
if target_name == PLACEHOLDER:
    validation_msgs.append("Select a target environment.")
if (
    selected_source
    and selected_target
    and selected_source["env_id"] == selected_target["env_id"]
):
    validation_msgs.append("Source and target must be different.")
if selected_target and _is_protected_target(selected_target["env_name"]):
    validation_msgs.append(f"Target cannot be {_PROTECTED_TARGET}.")
if selected_target and selected_target.get("locked"):
    validation_msgs.append(
        f"Target {selected_target['env_name']} is locked by an active clone run."
    )

can_trigger = (
    selected_user is not None
    and selected_source is not None
    and selected_target is not None
    and not validation_msgs
)

if selected_user and selected_source and selected_target and not validation_msgs:
    st.caption(
        f"Ready to clone **{selected_source['env_name']}** "
        f"→ **{selected_target['env_name']}** as **{selected_user['user_name']}**."
    )
elif validation_msgs and user_name != PLACEHOLDER:
    st.info(" ".join(validation_msgs))

with st.container(key="ca-execute-clone-actions"):
    if st.button(
        "Trigger job",
        type="primary",
        disabled=not can_trigger,
        key="exec_trigger",
        icon=":material/play_arrow:",
    ):
        try:
            result = trigger_clone_run(
                selected_user["user_id"],
                selected_source["env_id"],
                selected_target["env_id"],
            )
            run = get_run(result["clone_run_id"]) or result
            st.session_state["selected_run_id"] = run["clone_run_id"]
            st.session_state["selected_run"] = run
            st.session_state[f"auto_refresh_{run['clone_run_id']}"] = True
            st.session_state["_auto_refresh_run"] = run["clone_run_id"]
            st.query_params["run"] = str(run["clone_run_id"])
            st.success(
                result.get("message")
                or f"Clone run #{run['clone_run_id']} created."
            )
            goto_page("Run details")
        except Exception as exc:
            st.error(str(exc))

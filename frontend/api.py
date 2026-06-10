"""Tiny client for talking to the FastAPI backend from the Streamlit app.

Uses the standard library (``urllib``) so the frontend needs no extra
dependencies beyond ``python-dotenv`` (via ``config.settings``). All settings
are loaded from the repo-root ``.env`` file.
"""

import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config.settings import frontend

_cfg = frontend()
BACKEND_URL = _cfg.backend_url
API_KEY = _cfg.api_key
_HEALTH_TIMEOUT = _cfg.health_timeout_sec
_GET_TIMEOUT = _cfg.get_timeout_sec
_POST_TIMEOUT = _cfg.post_timeout_sec
_MAX_RUN_LIMIT = _cfg.max_run_limit


def _api_key_header() -> dict[str, str]:
    if not API_KEY:
        return {}
    return {"X-API-Key": API_KEY}


def _signed_url(path: str) -> str:
    """Build a backend URL, appending ``api_key`` for browser download links."""
    url = f"{BACKEND_URL}{path}"
    if not API_KEY:
        return url
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}{urllib.parse.urlencode({'api_key': API_KEY})}"


def check_backend_health(timeout: float | None = None) -> bool:
    """Return ``True`` if the backend ``/health`` endpoint responds with 200."""
    url = f"{BACKEND_URL}/health"
    try:
        with urllib.request.urlopen(url, timeout=timeout or _HEALTH_TIMEOUT) as resp:
            return resp.status == 200
    except Exception:
        return False


def _get_json(path: str, timeout: float | None = None):
    """GET a JSON resource from the backend. Raises on failure."""
    url = f"{BACKEND_URL}{path}"
    req = urllib.request.Request(url, headers=_api_key_header())
    with urllib.request.urlopen(req, timeout=timeout or _GET_TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _post_json(path: str, body: dict | None = None, timeout: float | None = None) -> dict:
    """POST JSON to the backend. Raises on failure."""
    url = f"{BACKEND_URL}{path}"
    payload = json.dumps(body or {}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json", **_api_key_header()},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout or _POST_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data if isinstance(data, dict) else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(body).get("detail", body)
        except json.JSONDecodeError:
            detail = body
        raise RuntimeError(detail) from exc


def _as_list(data, *keys: str) -> list[dict]:
    """Normalize a response that may be a bare list or a wrapped object
    like ``{"runs": [...]}`` into a plain list of dicts."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in keys:
            value = data.get(key)
            if isinstance(value, list):
                return value
    return []


def get_run_filters() -> dict[str, list[str]]:
    """Fetch distinct client, target, and user values for Run History filters."""
    data = _get_json("/api/v1/runs/filters")
    if isinstance(data, dict):
        return {
            "clients": data.get("clients") or [],
            "targets": data.get("targets") or [],
            "users": data.get("users") or [],
        }
    return {"clients": [], "targets": [], "users": []}


def get_runs(
    limit: int | None = None,
    client: str | None = None,
    target: str | None = None,
    user: str | None = None,
    start_date: date | None = None,
) -> list[dict]:
    """Fetch clone runs (newest execution first), optionally filtered."""
    params: dict[str, str | int] = {"limit": limit if limit is not None else _MAX_RUN_LIMIT}
    if client:
        params["client"] = client
    if target:
        params["target"] = target
    if user:
        params["user"] = user
    if start_date:
        params["start_date"] = start_date.isoformat()
    query = urllib.parse.urlencode(params)
    return _as_list(_get_json(f"/api/v1/runs?{query}"), "runs", "latest_runs")


def get_run(clone_run_id: int) -> dict | None:
    """Fetch a single clone run by id.

    Tries the dedicated ``/api/v1/runs/{id}`` endpoint first; if that is
    unavailable (older backend) it falls back to scanning the runs list.
    """
    try:
        data = _get_json(f"/api/v1/runs/{clone_run_id}")
        if isinstance(data, dict) and data.get("clone_run_id") is not None:
            return data
    except Exception:
        pass
    for run in get_runs():
        if run.get("clone_run_id") == clone_run_id:
            return run
    return None


def get_run_steps(clone_run_id: int) -> list[dict]:
    """Fetch the step rows (clone_function_run_status) for a clone run."""
    return _as_list(_get_json(f"/api/v1/runs/{clone_run_id}/steps"), "steps")


def get_step_detail(clone_run_id: int, clone_function_run_id: int) -> dict:
    """Fetch one function-step row and all attempts for that function."""
    data = _get_json(f"/api/v1/runs/{clone_run_id}/steps/{clone_function_run_id}")
    return data if isinstance(data, dict) else {}


def run_log_url(clone_run_id: int) -> str:
    """Backend download URL for a run's log (serves ``log_location``)."""
    return _signed_url(f"/api/v1/runs/{clone_run_id}/log")


def step_log_url(clone_run_id: int, clone_function_run_id: int) -> str:
    """Backend download URL for a function-step log."""
    return _signed_url(
        f"/api/v1/runs/{clone_run_id}/steps/{clone_function_run_id}/log"
    )


def abort_run(clone_run_id: int, clone_function_run_id: int | None = None) -> dict:
    """Insert ABORTED status for the run and the failed function step."""
    body = {}
    if clone_function_run_id is not None:
        body["clone_function_run_id"] = clone_function_run_id
    return _post_json(f"/api/v1/runs/{clone_run_id}/abort", body)


def skip_run(clone_run_id: int, clone_function_run_id: int | None = None) -> dict:
    """Insert SKIPPED status for the run and the failed function step."""
    body = {}
    if clone_function_run_id is not None:
        body["clone_function_run_id"] = clone_function_run_id
    return _post_json(f"/api/v1/runs/{clone_run_id}/skip", body)


def get_execute_clone_options() -> dict:
    """Fetch users and environments for the Execute Clone form."""
    data = _get_json("/api/v1/execute-clone/options")
    if isinstance(data, dict):
        return {
            "users": data.get("users") or [],
            "environments": data.get("environments") or [],
        }
    return {"users": [], "environments": []}


def trigger_clone_run(user_id: int, source_env_id: int, target_env_id: int) -> dict:
    """Trigger a clone run (locks target via ``create_clone_run``)."""
    return _post_json(
        "/api/v1/execute-clone/trigger",
        {
            "user_id": user_id,
            "source_env_id": source_env_id,
            "target_env_id": target_env_id,
        },
    )

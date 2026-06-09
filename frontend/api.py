"""Tiny client for talking to the FastAPI backend from the Streamlit app.

Uses the standard library (``urllib``) so the frontend needs no extra
dependencies. The backend base URL can be overridden with the ``BACKEND_URL``
environment variable.
"""

import json
import os
import urllib.request

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def check_backend_health(timeout: float = 2.0) -> bool:
    """Return ``True`` if the backend ``/health`` endpoint responds with 200."""
    url = f"{BACKEND_URL.rstrip('/')}/health"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


def _get_json(path: str, timeout: float = 5.0):
    """GET a JSON resource from the backend. Raises on failure."""
    url = f"{BACKEND_URL.rstrip('/')}{path}"
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


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


def get_runs(limit: int = 50) -> list[dict]:
    """Fetch clone runs (newest execution first)."""
    return _as_list(_get_json(f"/api/v1/runs?limit={limit}"), "runs", "latest_runs")


def get_run_steps(clone_run_id: int) -> list[dict]:
    """Fetch the step rows (clone_function_run_status) for a clone run."""
    return _as_list(_get_json(f"/api/v1/runs/{clone_run_id}/steps"), "steps")

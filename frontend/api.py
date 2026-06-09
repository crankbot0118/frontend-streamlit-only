"""Tiny client for talking to the FastAPI backend from the Streamlit app.

Uses the standard library (``urllib``) so the frontend needs no extra
dependencies. The backend base URL can be overridden with the ``BACKEND_URL``
environment variable.
"""

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

"""Authentication, path validation, rate limiting, and security headers."""

from __future__ import annotations

import secrets
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config.settings import api_security

_sec = api_security()

API_KEY = _sec.api_key
REQUIRE_API_KEY = _sec.require_api_key
ALLOWED_ORIGINS = _sec.allowed_origins
LOG_ALLOWED_ROOTS = _sec.log_allowed_roots
ALLOW_LOG_URL_REDIRECT = _sec.allow_log_url_redirect
RATE_LIMIT_REQUESTS = _sec.rate_limit_requests
RATE_LIMIT_WINDOW_SEC = _sec.rate_limit_window_sec
ENABLE_DOCS = _sec.enable_docs
API_MAX_RUN_LIMIT = _sec.max_run_limit

_PUBLIC_PATHS = {"/health"}


def verify_api_key(
    request: Request,
    x_api_key: Annotated[str | None, Header()] = None,
) -> None:
    """Require ``X-API-Key`` header on protected routes."""
    if request.url.path in _PUBLIC_PATHS:
        return
    if not API_KEY:
        if REQUIRE_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="API authentication is not configured",
            )
        return
    if not x_api_key or not secrets.compare_digest(x_api_key, API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )


def is_allowed_log_url(location: str) -> bool:
    return location.startswith(("http://", "https://")) and ALLOW_LOG_URL_REDIRECT


def resolve_local_log_path(location: str) -> Path:
    """Return a resolved file path only when it lies under ``LOG_ALLOWED_ROOTS``."""
    if location.startswith(("http://", "https://")):
        raise HTTPException(status_code=404, detail="Log not available")
    try:
        path = Path(location).expanduser().resolve(strict=False)
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=404, detail="Log not found") from exc
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Log not found")
    if not LOG_ALLOWED_ROOTS:
        return path
    for root in LOG_ALLOWED_ROOTS:
        if path == root or root in path.parents:
            return path
    raise HTTPException(status_code=403, detail="Log path not allowed")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int, window_seconds: int):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request, call_next):
        if request.url.path == "/health":
            return await call_next(request)
        client = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - self.window_seconds
        hits = [stamp for stamp in self._hits[client] if stamp > window_start]
        if len(hits) >= self.max_requests:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests"},
            )
        hits.append(now)
        self._hits[client] = hits
        return await call_next(request)

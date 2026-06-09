"""Authentication, path validation, rate limiting, and security headers."""

from __future__ import annotations

import os
import secrets
import time
from collections import defaultdict
from pathlib import Path
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Query, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

API_KEY = os.getenv("API_KEY", "").strip()
REQUIRE_API_KEY = os.getenv("REQUIRE_API_KEY", "true").lower() in ("1", "true", "yes")
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:8501,http://127.0.0.1:8501",
    ).split(",")
    if origin.strip()
]
LOG_ALLOWED_ROOTS = [
    Path(root).resolve()
    for root in os.getenv("LOG_ALLOWED_ROOTS", "/u02/shared").split(":")
    if root.strip()
]
ALLOW_LOG_URL_REDIRECT = os.getenv("ALLOW_LOG_URL_REDIRECT", "false").lower() in (
    "1",
    "true",
    "yes",
)
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "120"))
RATE_LIMIT_WINDOW_SEC = int(os.getenv("RATE_LIMIT_WINDOW_SEC", "60"))
ENABLE_DOCS = os.getenv("ENABLE_DOCS", "false").lower() in ("1", "true", "yes")

_PUBLIC_PATHS = {"/health"}


def verify_api_key(
    request: Request,
    x_api_key: Annotated[str | None, Header()] = None,
    api_key: Annotated[str | None, Query(alias="api_key")] = None,
) -> None:
    """Require ``X-API-Key`` header (or ``api_key`` query param for browser downloads)."""
    if request.url.path in _PUBLIC_PATHS:
        return
    if not API_KEY:
        if REQUIRE_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="API authentication is not configured",
            )
        return
    provided = x_api_key or api_key
    if not provided or not secrets.compare_digest(provided, API_KEY):
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

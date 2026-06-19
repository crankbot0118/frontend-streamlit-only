"""Central configuration for frontend and backend.

All values are read from the repo-root ``.env`` file. Application code does not
hardcode URLs, paths, or secrets.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

from config.errors import ConfigurationError

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = REPO_ROOT / ".env"
_env_loaded = False


def load_env(*, require_file: bool = True) -> None:
    """Load repo-root ``.env`` once (idempotent)."""
    global _env_loaded
    if _env_loaded:
        return
    if require_file and not ENV_FILE.is_file():
        raise ConfigurationError(
            f"Missing configuration file: {ENV_FILE}. "
            f"Create it with the required environment variables."
        )
    load_dotenv(ENV_FILE, override=False)
    _env_loaded = True


def _require(name: str) -> str:
    load_env()
    value = os.getenv(name, "").strip()
    if not value:
        raise ConfigurationError(
            f"Missing required environment variable {name!r}. "
            f"Set it in {ENV_FILE}."
        )
    return value


def _optional(name: str) -> str | None:
    load_env()
    value = os.getenv(name, "").strip()
    return value or None


def _bool(name: str) -> bool:
    return _require(name).lower() in ("1", "true", "yes")


def _int(name: str) -> int:
    raw = _require(name)
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigurationError(
            f"Environment variable {name!r} must be an integer, got {raw!r}."
        ) from exc


def _float(name: str) -> float:
    raw = _require(name)
    try:
        return float(raw)
    except ValueError as exc:
        raise ConfigurationError(
            f"Environment variable {name!r} must be a number, got {raw!r}."
        ) from exc


def _split_csv(name: str) -> list[str]:
    return [part.strip() for part in _require(name).split(",") if part.strip()]


def _split_path_list(name: str) -> list[str]:
    """Split a path list using OS path separator and ``:`` (for cross-platform)."""
    raw = _require(name)
    normalized = raw.replace(":", os.pathsep)
    return [part.strip() for part in normalized.split(os.pathsep) if part.strip()]


def is_protected_target_env(env_name: str, protected_name: str) -> bool:
    """Return True when ``env_name`` matches the protected target label (e.g. PROD)."""
    return (env_name or "").strip().upper() == protected_name.strip().upper()


@dataclass(frozen=True)
class LoggingSettings:
    level: int
    directory: Path
    to_file: bool
    max_bytes: int
    backup_count: int


@dataclass(frozen=True)
class DatabaseSettings:
    host: str
    port: int
    name: str
    user: str
    password: str
    min_conn: int
    max_conn: int

    @property
    def sqlalchemy_url(self) -> str:
        from urllib.parse import quote_plus

        password = quote_plus(self.password)
        return (
            f"postgresql+psycopg2://{self.user}:{password}"
            f"@{self.host}:{self.port}/{self.name}"
        )


@dataclass(frozen=True)
class ApiSecuritySettings:
    api_key: str
    require_api_key: bool
    allowed_origins: list[str]
    log_allowed_roots: list[Path]
    allow_log_url_redirect: bool
    rate_limit_requests: int
    rate_limit_window_sec: int
    enable_docs: bool
    max_run_limit: int
    protected_target_env_name: str
    host: str
    port: int


@dataclass(frozen=True)
class FrontendSettings:
    backend_url: str
    api_key: str
    health_timeout_sec: float
    get_timeout_sec: float
    post_timeout_sec: float
    max_run_limit: int
    run_details_refresh_sec: int
    protected_target_env_name: str


@lru_cache(maxsize=1)
def logging_config() -> LoggingSettings:
    load_env()
    level_name = (_optional("LOG_LEVEL") or "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    log_dir = Path(_optional("LOG_DIR") or str(REPO_ROOT / "logs"))
    return LoggingSettings(
        level=level,
        directory=log_dir,
        to_file=_bool("LOG_TO_FILE"),
        max_bytes=_int("LOG_MAX_BYTES"),
        backup_count=_int("LOG_BACKUP_COUNT"),
    )


@lru_cache(maxsize=1)
def database() -> DatabaseSettings:
    return DatabaseSettings(
        host=_require("DB_HOST"),
        port=_int("DB_PORT"),
        name=_require("DB_NAME"),
        user=_require("DB_USER"),
        password=_require("DB_PASSWORD"),
        min_conn=_int("DB_MIN_CONN"),
        max_conn=_int("DB_MAX_CONN"),
    )


@lru_cache(maxsize=1)
def api_security() -> ApiSecuritySettings:
    return ApiSecuritySettings(
        api_key=_optional("API_KEY") or "",
        require_api_key=_bool("REQUIRE_API_KEY"),
        allowed_origins=_split_csv("ALLOWED_ORIGINS"),
        log_allowed_roots=[Path(p).resolve() for p in _split_path_list("LOG_ALLOWED_ROOTS")],
        allow_log_url_redirect=_bool("ALLOW_LOG_URL_REDIRECT"),
        rate_limit_requests=_int("RATE_LIMIT_REQUESTS"),
        rate_limit_window_sec=_int("RATE_LIMIT_WINDOW_SEC"),
        enable_docs=_bool("ENABLE_DOCS"),
        max_run_limit=_int("API_MAX_RUN_LIMIT"),
        protected_target_env_name=_require("PROTECTED_TARGET_ENV_NAME"),
        host=_require("API_HOST"),
        port=_int("API_PORT"),
    )


@lru_cache(maxsize=1)
def frontend() -> FrontendSettings:
    sec = api_security()
    return FrontendSettings(
        backend_url=_require("BACKEND_URL").rstrip("/"),
        api_key=sec.api_key,
        health_timeout_sec=_float("API_HEALTH_TIMEOUT_SEC"),
        get_timeout_sec=_float("API_GET_TIMEOUT_SEC"),
        post_timeout_sec=_float("API_POST_TIMEOUT_SEC"),
        max_run_limit=sec.max_run_limit,
        run_details_refresh_sec=_int("RUN_DETAILS_REFRESH_SEC"),
        protected_target_env_name=sec.protected_target_env_name,
    )

"""Shared configuration loaded from repo-root ``.env``."""

from config.settings import (
    REPO_ROOT,
    ENV_FILE,
    ENV_EXAMPLE,
    load_env,
    logging_config,
    database,
    api_security,
    frontend,
    is_protected_target_env,
)
from config.errors import ConfigurationError, BackendError
from config.logging import setup_logging

__all__ = [
    "REPO_ROOT",
    "ENV_FILE",
    "ENV_EXAMPLE",
    "load_env",
    "logging_config",
    "database",
    "api_security",
    "frontend",
    "is_protected_target_env",
    "ConfigurationError",
    "BackendError",
    "setup_logging",
]

"""Shared configuration loaded from repo-root ``.env``."""

from config.settings import (
    REPO_ROOT,
    ENV_FILE,
    load_env,
    database,
    api_security,
    frontend,
    agent,
    agent_subprocess_env,
    is_protected_target_env,
)

__all__ = [
    "REPO_ROOT",
    "ENV_FILE",
    "load_env",
    "database",
    "api_security",
    "frontend",
    "agent",
    "agent_subprocess_env",
    "is_protected_target_env",
]

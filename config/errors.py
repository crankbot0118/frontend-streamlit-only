"""Shared exception types for configuration and backend communication."""


class ConfigurationError(RuntimeError):
    """Raised when repo-root ``.env`` is missing or invalid."""


class BackendError(RuntimeError):
    """Raised when a backend HTTP call fails."""

    def __init__(self, message: str, *, status_code: int | None = None, path: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.path = path

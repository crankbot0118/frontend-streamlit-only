"""Shared auto-refresh interval for all dashboard pages."""

from __future__ import annotations

from config.settings import frontend

PAGE_REFRESH_SEC = frontend().run_details_refresh_sec

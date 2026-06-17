"""Weekly clone KPI helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any

TERMINAL_STATUSES = frozenset({"COMPLETED", "FAILED", "ABORTED", "SKIPPED"})


def _as_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    return None


def _as_date(value: Any) -> date | None:
    dt = _as_dt(value)
    return dt.date() if dt else None


def week_bounds(ref: date | None = None) -> tuple[date, date]:
    """Monday–Sunday week containing ``ref`` (defaults to today)."""
    ref = ref or date.today()
    start = ref - timedelta(days=ref.weekday())
    return start, start + timedelta(days=6)


def previous_week_bounds(ref: date | None = None) -> tuple[date, date]:
    start, _ = week_bounds(ref)
    prev_start = start - timedelta(days=7)
    return prev_start, prev_start + timedelta(days=6)


def run_in_week(run: dict, start: date, end: date) -> bool:
    run_day = _as_date(run.get("start_date")) or _as_date(run.get("last_update"))
    return run_day is not None and start <= run_day <= end


def success_rate_stats(runs: list[dict]) -> tuple[float | None, int, int]:
    terminal = [r for r in runs if (r.get("status") or "").upper() in TERMINAL_STATUSES]
    completed = sum(1 for r in terminal if (r.get("status") or "").upper() == "COMPLETED")
    total = len(terminal)
    if total == 0:
        return None, 0, 0
    return round(100.0 * completed / total, 1), completed, total


def format_rate_delta(current: float | None, previous: float | None) -> tuple[str, str]:
    """Return (delta label, tone) where tone is up|down|neutral."""
    if current is None or previous is None:
        return "—", "neutral"
    diff = round(current - previous, 1)
    if diff == 0:
        return "0 pts", "neutral"
    tone = "up" if diff > 0 else "down"
    arrow = "▲" if diff > 0 else "▼"
    return f"{arrow} {abs(diff):g} pts", tone


def format_count_delta(current: int, previous: int) -> tuple[str, str]:
    """Return (percent delta label, tone) where tone is up|down|neutral."""
    if previous == 0:
        if current == 0:
            return "0%", "neutral"
        return "—", "neutral"
    diff_pct = round(100.0 * (current - previous) / previous, 1)
    if diff_pct == 0:
        return "0%", "neutral"
    tone = "up" if diff_pct > 0 else "down"
    arrow = "▲" if diff_pct > 0 else "▼"
    return f"{arrow} {abs(diff_pct):g}%", tone


@dataclass(frozen=True)
class WeeklySuccessKpi:
    week_start: date
    week_end: date
    rate: float | None
    completed: int
    total: int
    delta: str
    delta_tone: str


def weekly_success_kpi(runs: list[dict], ref: date | None = None) -> WeeklySuccessKpi:
    week_start, week_end = week_bounds(ref)
    prev_start, prev_end = previous_week_bounds(ref)
    week_runs = [r for r in runs if run_in_week(r, week_start, week_end)]
    prev_runs = [r for r in runs if run_in_week(r, prev_start, prev_end)]
    rate, completed, total = success_rate_stats(week_runs)
    prev_rate, _, _ = success_rate_stats(prev_runs)
    delta, tone = format_rate_delta(rate, prev_rate)
    return WeeklySuccessKpi(
        week_start=week_start,
        week_end=week_end,
        rate=rate,
        completed=completed,
        total=total,
        delta=delta,
        delta_tone=tone,
    )


@dataclass(frozen=True)
class WeeklyCloneCountKpi:
    week_start: date
    week_end: date
    count: int
    completed: int
    prev_count: int
    delta: str
    delta_tone: str


def weekly_clone_count_kpi(runs: list[dict], ref: date | None = None) -> WeeklyCloneCountKpi:
    week_start, week_end = week_bounds(ref)
    prev_start, prev_end = previous_week_bounds(ref)
    week_runs = [r for r in runs if run_in_week(r, week_start, week_end)]
    prev_runs = [r for r in runs if run_in_week(r, prev_start, prev_end)]
    count = len(week_runs)
    prev_count = len(prev_runs)
    completed = sum(
        1 for r in week_runs if (r.get("status") or "").upper() == "COMPLETED"
    )
    delta, tone = format_count_delta(count, prev_count)
    return WeeklyCloneCountKpi(
        week_start=week_start,
        week_end=week_end,
        count=count,
        completed=completed,
        prev_count=prev_count,
        delta=delta,
        delta_tone=tone,
    )

"""Weekly clone KPI calculations for the KPI Metrics dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any

# Hours from start to last_update for a run to count as SLA-compliant.
SLA_HOURS = 8.0

TERMINAL_STATUSES = frozenset({"COMPLETED", "FAILED", "ABORTED", "SKIPPED"})
OUTCOME_SUCCESS = frozenset({"COMPLETED", "SKIPPED"})


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


def week_bounds(ref: date) -> tuple[date, date]:
    """Monday–Sunday week containing ``ref``."""
    start = ref - timedelta(days=ref.weekday())
    return start, start + timedelta(days=6)


def previous_week_bounds(ref: date) -> tuple[date, date]:
    start, _ = week_bounds(ref)
    prev_start = start - timedelta(days=7)
    return prev_start, prev_start + timedelta(days=6)


def run_in_date_range(run: dict, start: date, end: date, *, field: str = "start_date") -> bool:
    run_day = _as_date(run.get(field))
    if run_day is None:
        run_day = _as_date(run.get("last_update"))
    if run_day is None:
        return False
    return start <= run_day <= end


def run_duration_hours(run: dict) -> float | None:
    start = _as_dt(run.get("start_date"))
    end = _as_dt(run.get("last_update"))
    if not start or not end or end < start:
        return None
    return (end - start).total_seconds() / 3600.0


def _status(run: dict) -> str:
    return (run.get("status") or "").upper()


@dataclass(frozen=True)
class WeekKpis:
    week_start: date
    week_end: date
    success_rate: float | None
    success_completed: int
    success_total: int
    clones_count: int
    sla_rate: float | None
    sla_compliant: int
    sla_total: int
    outcomes: dict[str, int]
    daily_completed: dict[str, int]
    prev_success_rate: float | None
    prev_clones_count: int
    prev_sla_rate: float | None


def _success_rate_stats(runs: list[dict]) -> tuple[float | None, int, int]:
    terminal = [r for r in runs if _status(r) in TERMINAL_STATUSES]
    completed = sum(1 for r in terminal if _status(r) == "COMPLETED")
    total = len(terminal)
    if total == 0:
        return None, 0, 0
    return round(100.0 * completed / total, 1), completed, total


def _sla_stats(runs: list[dict]) -> tuple[float | None, int, int]:
    finished = [r for r in runs if _status(r) == "COMPLETED"]
    if not finished:
        return None, 0, 0
    compliant = 0
    for run in finished:
        hours = run_duration_hours(run)
        if hours is not None and hours <= SLA_HOURS:
            compliant += 1
    total = len(finished)
    return round(100.0 * compliant / total, 1), compliant, total


def _outcome_counts(runs: list[dict]) -> dict[str, int]:
    counts = {"success": 0, "failed": 0, "aborted": 0}
    for run in runs:
        status = _status(run)
        if status in OUTCOME_SUCCESS:
            counts["success"] += 1
        elif status == "FAILED":
            counts["failed"] += 1
        elif status == "ABORTED":
            counts["aborted"] += 1
    return counts


def _daily_completed(runs: list[dict], week_start: date) -> dict[str, int]:
    labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    counts = {label: 0 for label in labels}
    for run in runs:
        if _status(run) != "COMPLETED":
            continue
        run_day = _as_date(run.get("last_update")) or _as_date(run.get("start_date"))
        if run_day is None or not (week_start <= run_day <= week_start + timedelta(days=6)):
            continue
        counts[labels[run_day.weekday()]] += 1
    return counts


def compute_week_kpis(runs: list[dict], ref: date) -> WeekKpis:
    week_start, week_end = week_bounds(ref)
    prev_start, prev_end = previous_week_bounds(ref)

    week_runs = [r for r in runs if run_in_date_range(r, week_start, week_end)]
    prev_runs = [r for r in runs if run_in_date_range(r, prev_start, prev_end)]

    success_rate, completed, total = _success_rate_stats(week_runs)
    prev_success_rate, _, _ = _success_rate_stats(prev_runs)

    sla_rate, sla_ok, sla_total = _sla_stats(week_runs)
    prev_sla_rate, _, _ = _sla_stats(prev_runs)

    return WeekKpis(
        week_start=week_start,
        week_end=week_end,
        success_rate=success_rate,
        success_completed=completed,
        success_total=total,
        clones_count=len(week_runs),
        sla_rate=sla_rate,
        sla_compliant=sla_ok,
        sla_total=sla_total,
        outcomes=_outcome_counts(week_runs),
        daily_completed=_daily_completed(week_runs, week_start),
        prev_success_rate=prev_success_rate,
        prev_clones_count=len(prev_runs),
        prev_sla_rate=prev_sla_rate,
    )


def format_delta(current: float | None, previous: float | None, *, unit: str = "pts") -> str:
    if current is None or previous is None:
        return "—"
    diff = round(current - previous, 1)
    if diff == 0:
        return f"0 {unit}"
    arrow = "▲" if diff > 0 else "▼"
    return f"{arrow} {abs(diff):g} {unit}"


def format_count_delta(current: int, previous: int) -> str:
    if previous == 0:
        if current == 0:
            return "0"
        return f"▲ {current}"
    diff_pct = round(100.0 * (current - previous) / previous)
    if diff_pct == 0:
        return "0%"
    arrow = "▲" if diff_pct > 0 else "▼"
    return f"{arrow} {abs(diff_pct)}%"

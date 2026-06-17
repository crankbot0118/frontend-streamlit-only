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


ACTIVITY_WEEKS = 12
OUTCOME_DAYS = 90
OUTCOME_FAILED = frozenset({"FAILED"})
OUTCOME_CANCELLED = frozenset({"ABORTED", "SKIPPED"})


def recent_week_ranges(weeks: int, ref: date | None = None) -> list[tuple[date, date, str]]:
    """Return ``weeks`` Mon–Sun ranges ending at the week containing ``ref``, oldest first."""
    ref = ref or date.today()
    current_start, _ = week_bounds(ref)
    ranges: list[tuple[date, date, str]] = []
    start = current_start
    for _ in range(weeks):
        ranges.append((start, start + timedelta(days=6), ""))
        start = start - timedelta(days=7)
    ranges.reverse()
    return [(s, e, f"W{i + 1}") for i, (s, e, _) in enumerate(ranges)]


def run_on_or_after(run: dict, cutoff: date) -> bool:
    run_day = _as_date(run.get("start_date")) or _as_date(run.get("last_update"))
    return run_day is not None and run_day >= cutoff


def run_duration_seconds(run: dict) -> float | None:
    start = _as_dt(run.get("start_date"))
    end = _as_dt(run.get("last_update"))
    if start is None or end is None or end <= start:
        return None
    return (end - start).total_seconds()


def format_duration(seconds: float | None) -> str:
    if seconds is None:
        return "—"
    total = int(seconds)
    hours, rem = divmod(total, 3600)
    minutes, _ = divmod(rem, 60)
    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m"
    return f"{total}s"


@dataclass(frozen=True)
class WeeklyActivityBucket:
    label: str
    week_start: date
    week_end: date
    successful: int
    failed: int


@dataclass(frozen=True)
class CloneActivityStats:
    weeks: tuple[WeeklyActivityBucket, ...]
    total_runs: int
    avg_duration_seconds: float | None
    throughput_per_day: float


def clone_activity_stats(
    runs: list[dict],
    *,
    weeks: int = ACTIVITY_WEEKS,
    ref: date | None = None,
) -> CloneActivityStats:
    ref = ref or date.today()
    week_ranges = recent_week_ranges(weeks, ref)
    window_start = week_ranges[0][0]
    window_runs = [
        r
        for r in runs
        if run_in_week(r, window_start, week_ranges[-1][1])
    ]
    buckets: list[WeeklyActivityBucket] = []
    for week_start, week_end, label in week_ranges:
        week_runs = [r for r in window_runs if run_in_week(r, week_start, week_end)]
        successful = sum(
            1 for r in week_runs if (r.get("status") or "").upper() == "COMPLETED"
        )
        failed = sum(
            1 for r in week_runs if (r.get("status") or "").upper() in OUTCOME_FAILED
        )
        buckets.append(
            WeeklyActivityBucket(
                label=label,
                week_start=week_start,
                week_end=week_end,
                successful=successful,
                failed=failed,
            )
        )

    durations = [
        run_duration_seconds(r)
        for r in window_runs
        if (r.get("status") or "").upper() == "COMPLETED"
    ]
    durations = [d for d in durations if d is not None]
    avg_duration = sum(durations) / len(durations) if durations else None

    day_span = max((ref - window_start).days + 1, 1)
    throughput = round(len(window_runs) / day_span, 1)

    return CloneActivityStats(
        weeks=tuple(buckets),
        total_runs=len(window_runs),
        avg_duration_seconds=avg_duration,
        throughput_per_day=throughput,
    )


@dataclass(frozen=True)
class OutcomeSlice:
    label: str
    count: int
    pct: float
    tone: str


@dataclass(frozen=True)
class OutcomeBreakdown:
    days: int
    success_rate: float | None
    slices: tuple[OutcomeSlice, ...]


def outcome_breakdown(
    runs: list[dict],
    *,
    days: int = OUTCOME_DAYS,
    ref: date | None = None,
) -> OutcomeBreakdown:
    ref = ref or date.today()
    cutoff = ref - timedelta(days=days - 1)
    scoped = [
        r
        for r in runs
        if run_on_or_after(r, cutoff)
        and (r.get("status") or "").upper() in TERMINAL_STATUSES
    ]
    successful = sum(
        1 for r in scoped if (r.get("status") or "").upper() == "COMPLETED"
    )
    failed = sum(
        1 for r in scoped if (r.get("status") or "").upper() in OUTCOME_FAILED
    )
    cancelled = sum(
        1 for r in scoped if (r.get("status") or "").upper() in OUTCOME_CANCELLED
    )
    total = successful + failed + cancelled
    if total == 0:
        empty = (
            OutcomeSlice("Successful", 0, 0.0, "ok"),
            OutcomeSlice("Failed", 0, 0.0, "bad"),
            OutcomeSlice("Cancelled", 0, 0.0, "muted"),
        )
        return OutcomeBreakdown(days=days, success_rate=None, slices=empty)

    def pct(count: int) -> float:
        return round(100.0 * count / total, 1)

    success_rate = pct(successful)
    slices = (
        OutcomeSlice("Successful", successful, success_rate, "ok"),
        OutcomeSlice("Failed", failed, pct(failed), "bad"),
        OutcomeSlice("Cancelled", cancelled, pct(cancelled), "muted"),
    )
    return OutcomeBreakdown(days=days, success_rate=success_rate, slices=slices)

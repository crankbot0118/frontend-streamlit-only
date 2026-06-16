"""KPI Metrics — weekly clone performance dashboard."""

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from api import get_runs
from config.settings import frontend
from kpi_helpers import (
    SLA_HOURS,
    compute_week_kpis,
    format_count_delta,
    format_delta,
    week_bounds,
)
from styles import (
    emit_html,
    goto_page,
    kpi_card_html,
    kpi_cards_row_html,
    latest_runs_table_html,
    outcome_donut_html,
    render_title,
)
from ui_errors import show_error

_MAX = frontend().max_run_limit


def _delta_tone(current: float | None, previous: float | None) -> str:
    if current is None or previous is None:
        return "neutral"
    if current > previous:
        return "up"
    if current < previous:
        return "down"
    return "neutral"


def _count_delta_tone(current: int, previous: int) -> str:
    if current > previous:
        return "up"
    if current < previous:
        return "down"
    return "neutral"


def _week_label(start: date, end: date) -> str:
    return f"{start.strftime('%d %b')} – {end.strftime('%d %b %Y')}"


render_title(
    "KPI Metrics",
    subtitle="Weekly clone performance, outcomes, and recent activity.",
)

col_week, col_sla = st.columns([1, 1], gap="small", vertical_alignment="bottom")
with col_week:
    ref_date = st.date_input(
        "Week containing",
        value=date.today(),
        format="DD/MM/YYYY",
        key="kpi_week_ref",
    )
with col_sla:
    st.caption(f"SLA target: completed within {SLA_HOURS:g} hours")

week_start, week_end = week_bounds(ref_date)
fetch_start = week_start - timedelta(days=7)

try:
    runs = get_runs(limit=_MAX, start_date=fetch_start, end_date=week_end)
except Exception as exc:
    show_error(exc, context="Could not load runs for KPI metrics")
    runs = []

kpis = compute_week_kpis(runs, ref_date)

st.caption(f"Showing week {_week_label(kpis.week_start, kpis.week_end)}")

success_val = f"{kpis.success_rate:.1f}" if kpis.success_rate is not None else "—"
sla_val = f"{kpis.sla_rate:.1f}" if kpis.sla_rate is not None else "—"

cards = [
    kpi_card_html(
        "Clone success rate",
        success_val,
        unit="%" if kpis.success_rate is not None else "",
        delta=format_delta(kpis.success_rate, kpis.prev_success_rate),
        delta_tone=_delta_tone(kpis.success_rate, kpis.prev_success_rate),
        note=f"{kpis.success_completed} of {kpis.success_total} jobs",
        icon="✓",
    ),
    kpi_card_html(
        "Clones this week",
        str(kpis.clones_count),
        delta=format_count_delta(kpis.clones_count, kpis.prev_clones_count),
        delta_tone=_count_delta_tone(kpis.clones_count, kpis.prev_clones_count),
        note=f"{kpis.prev_clones_count} prior week",
        icon="⏱",
    ),
    kpi_card_html(
        "SLA compliance rate",
        sla_val,
        unit="%" if kpis.sla_rate is not None else "",
        delta=format_delta(kpis.sla_rate, kpis.prev_sla_rate),
        delta_tone=_delta_tone(kpis.sla_rate, kpis.prev_sla_rate),
        note=f"{kpis.sla_compliant} of {kpis.sla_total} on-time",
        icon="🛡",
    ),
]
emit_html(kpi_cards_row_html(cards))

chart_col, pie_col = st.columns([1.35, 1], gap="small")
with chart_col:
    with st.container(key="ca-kpi-activity"):
        st.html(
            f'<div class="ca-kpi-panel">'
            f'<div class="ca-kpi-panel-title">Clone activity</div>'
            f'<div class="ca-kpi-panel-sub">Completed jobs per day · {_week_label(kpis.week_start, kpis.week_end)}</div>'
            f"</div>"
        )
        daily_df = pd.DataFrame(
            {"Completed": list(kpis.daily_completed.values())},
            index=list(kpis.daily_completed.keys()),
        )
        st.bar_chart(daily_df, height=220, color="#e87511")

with pie_col:
    with st.container(key="ca-kpi-outcome"):
        st.html(
            '<div class="ca-kpi-panel">'
            '<div class="ca-kpi-panel-title">Outcome breakdown</div>'
            f'<div class="ca-kpi-panel-sub">This week · success, failed, aborted</div>'
            f"{outcome_donut_html(kpis.outcomes, kpis.success_rate)}"
            "</div>"
        )

st.html(
    '<div class="ca-kpi-panel" style="margin-top:0;">'
    '<div class="ca-kpi-panel-title">Latest runs</div>'
    '<div class="ca-kpi-panel-sub">Most recent clone jobs (limit 5)</div>'
    "</div>"
)

latest = sorted(
    runs,
    key=lambda r: (r.get("last_update") or "", r.get("clone_run_id") or 0),
    reverse=True,
)[:5]

if latest:
    emit_html(latest_runs_table_html(latest))
    if st.button("View all in Run History", key="kpi_go_history", type="tertiary"):
        goto_page("Run History")
else:
    st.caption("No runs to show yet.")

"""Home page."""

from datetime import date, timedelta

import streamlit as st

from api import get_runs
from config.settings import frontend
from home_charts import (
    clone_activity_figure,
    clone_activity_header_html,
    outcome_donut_figure,
    outcome_header_html,
    outcome_legend_html,
    plotly_config,
)
from kpi_helpers import (
    OUTCOME_DAYS,
    clone_activity_stats,
    outcome_breakdown,
    week_bounds,
    weekly_clone_count_kpi,
    weekly_success_kpi,
)
from styles import (
    count_kpi_card_dict,
    goto_page,
    home_kpis_html,
    placeholder_kpi_card_dict,
    render_run_card,
    render_title,
    success_kpi_card_dict,
)
from ui_errors import show_error

HOME_KPI_COUNT = 4
HOME_KPI_ICONS = ("check", "layers", "check", "layers")
HOME_RECENT_RUNS_LIMIT = 5

render_title(
    "VClone",
    subtitle="Orchestrate, monitor, and audit end-to-end Oracle EBS clone pipelines with full lifecycle visibility.",
)

week_start, week_end = week_bounds()
chart_fetch_start = date.today() - timedelta(days=OUTCOME_DAYS)
kpi_fetch_start = week_start - timedelta(days=7)
fetch_start = min(chart_fetch_start, kpi_fetch_start)

try:
    runs = get_runs(
        limit=frontend().max_run_limit,
        start_date=fetch_start,
        end_date=week_end,
    )
except Exception as exc:
    show_error(exc, context="Could not load weekly KPI data")
    runs = []

try:
    recent_runs = get_runs(limit=HOME_RECENT_RUNS_LIMIT)
except Exception as exc:
    show_error(exc, context="Could not load recent runs")
    recent_runs = []

success_kpi = weekly_success_kpi(runs)
count_kpi = weekly_clone_count_kpi(runs)

cards = [
    success_kpi_card_dict("Weekly success rate", success_kpi, icon=HOME_KPI_ICONS[0]),
    count_kpi_card_dict("Clones this week", count_kpi, icon=HOME_KPI_ICONS[1]),
]
for index in range(3, HOME_KPI_COUNT + 1):
    placeholder_titles = ("Engineer hours saved", "SLA compliance")
    title = placeholder_titles[index - 3] if index - 3 < len(placeholder_titles) else f"KPI{index}"
    cards.append(
        placeholder_kpi_card_dict(
            title,
            icon=HOME_KPI_ICONS[(index - 1) % len(HOME_KPI_ICONS)],
        )
    )

activity = clone_activity_stats(runs)
outcome = outcome_breakdown(runs)

with st.container(key="ca_home_dashboard"):
    st.markdown(home_kpis_html(cards), unsafe_allow_html=True)
    activity_col, outcome_col = st.columns([2, 1], gap="small")
    with activity_col:
        with st.container(key="ca_clone_activity"):
            st.markdown(clone_activity_header_html(activity), unsafe_allow_html=True)
            st.plotly_chart(
                clone_activity_figure(activity),
                use_container_width=True,
                config=plotly_config(),
            )
        with st.container(key="ca_home_recent_runs"):
            st.markdown(
                '<div class="ca-home-chart-head">'
                '<div class="ca-home-chart-title">Recent runs</div>'
                "</div>",
                unsafe_allow_html=True,
            )
            if not recent_runs:
                st.caption("No runs to show yet.")
            else:
                with st.container(key="ca-runs"):
                    for run in recent_runs:
                        if render_run_card(run, key_prefix="home_", compact=True):
                            st.session_state["selected_run_id"] = run["clone_run_id"]
                            st.session_state["selected_run"] = run
                            st.session_state[f"auto_refresh_{run['clone_run_id']}"] = True
                            st.session_state["_auto_refresh_run"] = run["clone_run_id"]
                            st.query_params["run"] = str(run["clone_run_id"])
                            goto_page("Run details")
    with outcome_col:
        with st.container(key="ca_outcome_breakdown"):
            st.markdown(outcome_header_html(outcome), unsafe_allow_html=True)
            st.plotly_chart(
                outcome_donut_figure(outcome),
                use_container_width=True,
                config=plotly_config(),
            )
            st.markdown(outcome_legend_html(outcome), unsafe_allow_html=True)
        with st.container(key="ca_home_upcoming_schedule"):
            st.markdown(
                '<div class="ca-home-chart-head">'
                '<div class="ca-home-chart-title">Upcoming schedule</div>'
                "</div>"
                '<span class="ca-soon ca-home-soon">Coming soon!</span>',
                unsafe_allow_html=True,
            )

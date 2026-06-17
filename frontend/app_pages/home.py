"""Home page."""

from datetime import timedelta

import streamlit as st

from api import get_runs
from config.settings import frontend
from kpi_helpers import week_bounds, weekly_clone_count_kpi, weekly_success_kpi
from styles import (
    count_kpi_card_dict,
    home_kpis_html,
    placeholder_kpi_card_dict,
    render_title,
    success_kpi_card_dict,
)
from ui_errors import show_error

HOME_KPI_COUNT = 4
HOME_KPI_ICONS = ("check", "layers", "check", "layers")

render_title(
    "VClone",
    subtitle="Orchestrate, monitor, and audit end-to-end Oracle EBS clone pipelines with full lifecycle visibility.",
)

week_start, week_end = week_bounds()
fetch_start = week_start - timedelta(days=7)

try:
    runs = get_runs(
        limit=frontend().max_run_limit,
        start_date=fetch_start,
        end_date=week_end,
    )
except Exception as exc:
    show_error(exc, context="Could not load weekly KPI data")
    runs = []

success_kpi = weekly_success_kpi(runs)
count_kpi = weekly_clone_count_kpi(runs)

cards = [
    success_kpi_card_dict("KPI1", success_kpi, icon=HOME_KPI_ICONS[0]),
    count_kpi_card_dict("KPI2", count_kpi, icon=HOME_KPI_ICONS[1]),
]
for index in range(3, HOME_KPI_COUNT + 1):
    cards.append(
        placeholder_kpi_card_dict(
            f"KPI{index}",
            icon=HOME_KPI_ICONS[(index - 1) % len(HOME_KPI_ICONS)],
        )
    )

st.markdown(home_kpis_html(cards), unsafe_allow_html=True)

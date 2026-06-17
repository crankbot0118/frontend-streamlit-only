"""Home page."""

from datetime import timedelta

import streamlit as st

from api import get_runs
from config.settings import frontend
from kpi_helpers import week_bounds, weekly_clone_count_kpi, weekly_success_kpi
from styles import home_kpis_html, render_title
from ui_errors import show_error

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
st.markdown(home_kpis_html(success_kpi, count_kpi), unsafe_allow_html=True)

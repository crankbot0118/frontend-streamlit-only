"""Clone Automation dashboard — home page."""

import streamlit as st

from styles import apply_global_styles, render_logo, render_sidebar_nav, render_title

st.set_page_config(
    page_title="Clone automation dashboard",
    page_icon=":material/precision_manufacturing:",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_global_styles()

with st.sidebar:
    render_logo()
    render_sidebar_nav()

render_title(
    "Clone automation dashboard",
    subtitle="Monitor, run, and review your automated clone jobs.",
)

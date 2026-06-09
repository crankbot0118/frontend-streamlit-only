"""Clone Automation dashboard — home page."""

import streamlit as st

from styles import (
    DEFAULT_PAGE,
    apply_global_styles,
    render_logo,
    render_sidebar_nav,
    render_title,
)

st.set_page_config(
    page_title="Clone automation dashboard",
    page_icon=":material/precision_manufacturing:",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_global_styles()

if "active_page" not in st.session_state:
    st.session_state["active_page"] = DEFAULT_PAGE

with st.sidebar:
    render_logo()
    render_sidebar_nav()

active_page = st.session_state["active_page"]
render_title(active_page)

st.write(f"{active_page} content goes here.")

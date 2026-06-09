import streamlit as st

from components import render_page_header
from styles import apply_global_styles

st.set_page_config(
    page_title="Clone Automation Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_global_styles()
render_page_header("Clone Automation Dashboard")
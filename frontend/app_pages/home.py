"""Home page."""

import streamlit as st

from styles import render_title

render_title(
    "VClone",
    subtitle="Orchestrate, monitor, and audit end-to-end Oracle EBS clone pipelines with full lifecycle visibility.",
)

st.write("Home content goes here.")

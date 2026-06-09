"""Run History page."""

import streamlit as st

from styles import render_title

render_title(
    "Run History",
    subtitle="Review past clone runs and their outcomes.",
)

st.write("Run History content goes here.")

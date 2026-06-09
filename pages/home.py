"""Home page."""

import streamlit as st

from styles import render_title

render_title(
    "Clone automation dashboard",
    subtitle="Monitor, run, and review your automated clone jobs.",
)

st.write("Home content goes here.")

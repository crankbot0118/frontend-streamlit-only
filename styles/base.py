"""Base utilities for injecting modular CSS into Streamlit."""

import streamlit as st


def inject_css(*modules: str) -> None:
    """Combine and inject one or more CSS module strings."""
    combined = "\n".join(module.strip() for module in modules if module.strip())
    if combined:
        st.markdown(f"<style>{combined}</style>", unsafe_allow_html=True)

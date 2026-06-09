import streamlit as st

from styles.layout import PAGE_HEADER_CLASS
from styles.typography import PAGE_TITLE_CLASS


def render_page_header(title: str) -> None:
    st.markdown(
        f"""
        <header class="{PAGE_HEADER_CLASS}">
            <h1 class="{PAGE_TITLE_CLASS}">{title}</h1>
        </header>
        """,
        unsafe_allow_html=True,
    )

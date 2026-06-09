"""Clone Automation dashboard — multipage entry point.

Defines the page registry and renders the shared, custom-styled sidebar.
The default Streamlit nav is hidden (``position="hidden"``) so our own
sidebar in ``render_sidebar_nav`` is the only navigation.
"""

import streamlit as st

from styles import (
    apply_global_styles,
    build_pages,
    render_logo,
    render_sidebar_nav,
)

st.set_page_config(
    page_title="Clone automation dashboard",
    page_icon=":material/precision_manufacturing:",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_global_styles()

pages = build_pages()
pg = st.navigation(list(pages.values()), position="hidden")

with st.sidebar:
    render_logo()
    render_sidebar_nav(pages, current_title=pg.title)

pg.run()

"""Clone Automation dashboard — multipage entry point."""

import sys
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

from config.errors import ConfigurationError
from config.logging import setup_logging

log = setup_logging("frontend")

try:
    from config.settings import ENV_EXAMPLE, ENV_FILE, load_env

    load_env()
except ConfigurationError as exc:
    st.set_page_config(page_title="Clone automation dashboard", layout="wide")
    st.error(str(exc))
    if ENV_EXAMPLE.is_file():
        st.info(f"Copy `{ENV_EXAMPLE.name}` to `{ENV_FILE.name}` in the repo root, then restart.")
    st.stop()

if hasattr(st, "set_theme"):
    st.set_theme(
        base="light",
        primary_color="#e87511",
        background_color="#ffffff",
        secondary_background_color="#f6f7f8",
        text_color="#131516",
    )

from api import check_backend_health
from styles import (
    apply_global_styles,
    build_pages,
    render_logo,
    render_sidebar_nav,
    render_status,
)

st.set_page_config(
    page_title="Clone automation dashboard",
    page_icon=":material/precision_manufacturing:",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_global_styles()

pages = build_pages()
st.session_state["_pages"] = pages
pg = st.navigation(list(pages.values()), position="hidden")

with st.sidebar:
    render_logo()
    render_sidebar_nav(pages, current_title=pg.title)
    is_live = check_backend_health()
    if not is_live:
        log.warning("Backend health check failed for %s", pg.title)
    render_status(is_live, datetime.now(timezone.utc))

pg.run()

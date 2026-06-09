"""Reusable custom CSS for the Clone Automation dashboard.

Import and call ``apply_global_styles()`` once near the top of any page
(after ``st.set_page_config``) to get consistent styling across the app.
"""

import base64
from pathlib import Path

import streamlit as st

BRAND_ORANGE = "#e87511"
BRAND_INK = "#131516"

_GLOBAL_CSS = f"""
<style>
  /* Pull the page content to the very top, no wasted space. */
  [data-testid="stMainBlockContainer"] {{
      padding-top: 1.2rem;
      padding-bottom: 2rem;
  }}

  /* Collapse the empty default header bar that pushes content down. */
  [data-testid="stHeader"] {{
      height: 0;
      background: transparent;
  }}

  /* Persistent sidebar: hide the collapse control so it stays expanded. */
  [data-testid="stSidebarCollapseButton"] {{
      display: none !important;
  }}

  /* Fixed-width, non-resizable sidebar. */
  [data-testid="stSidebarResizeHandle"] {{
      display: none !important;
  }}

  [data-testid="stSidebar"] {{
      width: 244px !important;
      min-width: 244px !important;
      max-width: 244px !important;
  }}

  /* Collapse the empty sidebar header so content sits at the very top. */
  [data-testid="stSidebarHeader"] {{
      height: 0;
      min-height: 0;
      padding: 0;
  }}

  /* Sidebar content top-flush, matching the main title. */
  [data-testid="stSidebarUserContent"] {{
      padding-top: 1.2rem;
  }}

  /* Logo block, left-aligned to match render_title. */
  .ca-logo {{
      margin: 0 0 0.9rem 0;
      padding: 0;
  }}

  .ca-logo img {{
      width: 170px;
      max-width: 100%;
      height: auto;
      display: block;
  }}

  /* Page title row, flush to the top. */
  .ca-title {{
      display: flex;
      align-items: center;
      gap: 0.65rem;
      margin: 0 0 0.25rem 0;
      padding: 0;
      line-height: 1.1;
  }}

  .ca-title h1 {{
      margin: 0;
      padding: 0;
      font-size: 2.1rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      color: {BRAND_INK};
  }}

  /* Accent bar under the title. */
  .ca-title-rule {{
      height: 3px;
      width: 100%;
      border: none;
      margin: 0.4rem 0 1.4rem 0;
      border-radius: 999px;
      background: linear-gradient(90deg, {BRAND_ORANGE} 0%, rgba(232,117,17,0.15) 100%);
  }}

  .ca-subtitle {{
      margin: 0;
      color: #5b6166;
      font-size: 0.95rem;
  }}

  /* ---------- Sidebar navigation ---------- */

  /* Tighten vertical spacing and keep every block left-aligned. */
  .st-key-ca-nav [data-testid="stVerticalBlock"] {{
      gap: 0.1rem;
      align-items: stretch;
  }}

  .st-key-ca-nav [data-testid="stElementContainer"] {{
      align-items: flex-start;
      text-align: left;
  }}

  /* Borderless, left-aligned link-style nav buttons (descendant selectors so
     we catch the button regardless of intermediate wrappers). */
  .st-key-ca-nav .stButton button {{
      display: flex !important;
      align-items: center !important;
      justify-content: flex-start !important;
      text-align: left !important;
      width: 100% !important;
      background: transparent !important;
      border: none !important;
      box-shadow: none !important;
      outline: none !important;
      gap: 0.7rem;
      padding: 0.45rem 0.55rem;
      border-radius: 8px;
      color: {BRAND_INK};
  }}

  /* Stop Streamlit from centering the label inside the button. */
  .st-key-ca-nav .stButton button > div,
  .st-key-ca-nav .stButton button [data-testid="stMarkdownContainer"] {{
      width: 100%;
      display: flex !important;
      justify-content: flex-start !important;
      text-align: left !important;
  }}

  .st-key-ca-nav .stButton button p {{
      margin: 0;
      font-weight: 600;
      font-size: 0.98rem;
      text-align: left !important;
  }}

  .st-key-ca-nav .stButton button:hover {{
      background: rgba(232, 117, 17, 0.12) !important;
      color: {BRAND_ORANGE};
  }}

  .st-key-ca-nav .stButton button:hover svg,
  .st-key-ca-nav .stButton button:hover p {{
      color: {BRAND_ORANGE};
  }}

  /* Group dropdowns: fully borderless / no box, blend into the sidebar. */
  .st-key-ca-nav [data-testid="stExpander"],
  .st-key-ca-nav [data-testid="stExpander"] details {{
      border: none !important;
      box-shadow: none !important;
      outline: none !important;
      background: transparent !important;
  }}

  .st-key-ca-nav [data-testid="stExpander"] summary {{
      display: flex !important;
      align-items: center !important;
      justify-content: flex-start !important;
      gap: 0.5rem;
      padding: 0.45rem 0.55rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.03em;
      font-size: 0.78rem;
      color: #6b7177;
      background: transparent !important;
      border: none !important;
      box-shadow: none !important;
      outline: none !important;
  }}

  .st-key-ca-nav [data-testid="stExpander"] summary:hover,
  .st-key-ca-nav [data-testid="stExpander"] summary:focus,
  .st-key-ca-nav [data-testid="stExpander"] summary:focus-visible {{
      color: {BRAND_INK};
      background: transparent !important;
      border: none !important;
      box-shadow: none !important;
      outline: none !important;
  }}

  /* Brand-colored chevron, moved to the left of the label. */
  .st-key-ca-nav [data-testid="stExpander"] summary svg {{
      order: -1;
      color: {BRAND_ORANGE};
      fill: {BRAND_ORANGE};
  }}

  /* Left-align the summary label text too. */
  .st-key-ca-nav [data-testid="stExpander"] summary p,
  .st-key-ca-nav [data-testid="stExpander"] summary span {{
      text-align: left !important;
  }}

  /* Indent the items nested inside a group. */
  .st-key-ca-nav [data-testid="stExpanderDetails"] {{
      padding-left: 0.6rem;
  }}

  /* Keep the divider, tinted to match the logo. */
  .st-key-ca-nav [data-testid="stDivider"] hr {{
      margin: 0.5rem 0;
      border-color: rgba(232, 117, 17, 0.25);
  }}
</style>
"""


def apply_global_styles() -> None:
    """Inject the shared CSS into the current page."""
    st.html(_GLOBAL_CSS)


def render_logo(path: str = "assets/logo.svg", width: int = 170) -> None:
    """Render the SVG logo, top-flush and left-aligned like ``render_title``.

    Reads the SVG from ``assets/`` and embeds it as a data URI so it renders
    inline (typically inside the sidebar).
    """
    svg = Path(path).read_text(encoding="utf-8")
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    st.html(
        f"""
        <div class="ca-logo">
          <img src="data:image/svg+xml;base64,{b64}" alt="Clone automation logo"
               style="width:{width}px;" />
        </div>
        """
    )


def render_sidebar_nav() -> None:
    """Render the sidebar navigation: link-style items with Material icons
    and collapsible groups, styled to look borderless and clean.

    Call ``apply_global_styles()`` before this so the CSS is available, and
    call this inside a ``with st.sidebar:`` block.
    """
    with st.container(key="ca-nav"):
        st.button(
            "Dashboard",
            icon=":material/space_dashboard:",
            width="stretch",
            key="nav_dashboard",
        )

        with st.expander("Admin", expanded=True):
            st.button("Accounts", icon=":material/work:", width="stretch", key="nav_accounts")
            st.button("Team", icon=":material/group:", width="stretch", key="nav_team")
            st.button("Targets", icon=":material/dns:", width="stretch", key="nav_targets")

        with st.expander("Clone Setup", expanded=True):
            st.button("Database", icon=":material/database:", width="stretch", key="nav_database")
            st.button("EBS Config", icon=":material/deployed_code:", width="stretch", key="nav_ebs")
            st.button(
                "Connections",
                icon=":material/power:",
                width="stretch",
                key="nav_connections",
            )

        st.divider()

        st.button(
            "Execute Clone",
            icon=":material/play_arrow:",
            width="stretch",
            key="nav_execute",
        )
        st.button("Run History", icon=":material/history:", width="stretch", key="nav_history")


def render_title(title: str, subtitle: str | None = None) -> None:
    """Render a top-flush page title with an accent rule.

    Call ``apply_global_styles()`` before this so the CSS is available.
    """
    subtitle_html = f'<p class="ca-subtitle">{subtitle}</p>' if subtitle else ""
    st.html(
        f"""
        <div class="ca-title">
          <h1>{title}</h1>
        </div>
        {subtitle_html}
        <hr class="ca-title-rule" />
        """
    )

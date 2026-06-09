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

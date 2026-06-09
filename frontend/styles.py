"""Reusable custom CSS for the Clone Automation dashboard.

Import and call ``apply_global_styles()`` once near the top of any page
(after ``st.set_page_config``) to get consistent styling across the app.
"""

import base64
from pathlib import Path

import streamlit as st

BRAND_ORANGE = "#e87511"
BRAND_INK = "#131516"

# Repo root is the parent of the ``frontend/`` package that holds this file.
REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LOGO_PATH = REPO_ROOT / "assets" / "logo.svg"

_GLOBAL_CSS = f"""
<style>
  /* Pull the page content to the very top, no wasted space, and trim the
     wide left/right gutters so content sits closer to the sidebar. */
  [data-testid="stMainBlockContainer"] {{
      padding-top: 1.2rem;
      padding-bottom: 2rem;
      padding-left: 1.5rem;
      padding-right: 1.5rem;
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
      width: 264px !important;
      min-width: 264px !important;
      max-width: 264px !important;
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
      font-size: 2.6rem;
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

  /* Active item (rendered as a primary button) — brand highlight. */
  .st-key-ca-nav .stButton button[kind="primary"] {{
      background: rgba(232, 117, 17, 0.14) !important;
      box-shadow: inset 3px 0 0 {BRAND_ORANGE} !important;
      color: {BRAND_ORANGE} !important;
  }}

  .st-key-ca-nav .stButton button[kind="primary"] p {{
      color: {BRAND_ORANGE} !important;
      font-weight: 700;
  }}

  .st-key-ca-nav .stButton button[kind="primary"] svg {{
      color: {BRAND_ORANGE} !important;
      fill: {BRAND_ORANGE} !important;
  }}

  /* Disabled ("coming soon") items: muted, not clickable, no hover accent. */
  .st-key-ca-nav .stButton button:disabled,
  .st-key-ca-nav .stButton button[disabled] {{
      opacity: 1 !important;
      cursor: not-allowed !important;
      background: transparent !important;
      color: #9aa0a6 !important;
  }}

  .st-key-ca-nav .stButton button:disabled p,
  .st-key-ca-nav .stButton button:disabled svg {{
      color: #9aa0a6 !important;
      fill: #9aa0a6 !important;
  }}

  /* Small yellow "Coming soon!" highlight at the top of the Admin group. */
  .ca-soon {{
      display: inline-block;
      margin: 0 0 0.4rem 0.55rem;
      padding: 0.05rem 0.45rem;
      border-radius: 6px;
      background: #fff3cd;
      color: #8a6500;
      font-size: 0.66rem;
      font-weight: 700;
      letter-spacing: 0.02em;
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


def render_logo(path: str | Path | None = None, width: int = 170) -> None:
    """Render the SVG logo, top-flush and left-aligned like ``render_title``.

    Reads the SVG from the repo-root ``assets/`` folder (resolved absolutely so
    it works regardless of the current working directory) and embeds it as a
    data URI so it renders inline (typically inside the sidebar).
    """
    svg = Path(path or DEFAULT_LOGO_PATH).read_text(encoding="utf-8")
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    st.html(
        f"""
        <div class="ca-logo">
          <img src="data:image/svg+xml;base64,{b64}" alt="Clone automation logo"
               style="width:{width}px;" />
        </div>
        """
    )


DEFAULT_PAGE = "Home"

# Single source of truth for navigation: drives both the real ``st.Page``
# registry (build_pages) and the custom sidebar (render_sidebar_nav).
NAV: list[dict] = [
    {"kind": "item", "title": "Home", "icon": "space_dashboard",
     "key": "nav_home", "module": "pages/home.py"},
    {"kind": "group", "title": "Admin", "badge": "Coming soon!", "items": [
        {"title": "Clients", "icon": "work", "key": "nav_clients",
         "module": "pages/clients.py", "disabled": True},
        {"title": "Team", "icon": "group", "key": "nav_team",
         "module": "pages/team.py", "disabled": True},
        {"title": "Targets", "icon": "dns", "key": "nav_targets",
         "module": "pages/targets.py", "disabled": True},
    ]},
    {"kind": "group", "title": "Clone Setup", "items": [
        {"title": "DB Config", "icon": "database", "key": "nav_db", "module": "pages/db_config.py"},
        {"title": "EBS Config", "icon": "deployed_code", "key": "nav_ebs", "module": "pages/ebs_config.py"},
        {"title": "Integrations", "icon": "hub", "key": "nav_integrations", "module": "pages/integrations.py"},
    ]},
    {"kind": "divider"},
    {"kind": "item", "title": "Execute Clone", "icon": "play_arrow",
     "key": "nav_execute", "module": "pages/execute_clone.py"},
    {"kind": "item", "title": "Run History", "icon": "history",
     "key": "nav_history", "module": "pages/run_history.py"},
]


def _iter_nav_items(nav: list[dict] = NAV):
    """Yield every clickable nav item (flattening groups)."""
    for entry in nav:
        if entry["kind"] == "item":
            yield entry
        elif entry["kind"] == "group":
            yield from entry["items"]


def build_pages() -> dict:
    """Build the ``st.Page`` registry keyed by page title.

    Pass ``list(build_pages().values())`` to ``st.navigation``.
    """
    pages = {}
    for item in _iter_nav_items():
        pages[item["title"]] = st.Page(
            item["module"],
            title=item["title"],
            icon=f":material/{item['icon']}:",
            default=(item["title"] == DEFAULT_PAGE),
        )
    return pages


def _nav_link(pages: dict, item: dict, current_title: str) -> None:
    """A single link-style nav button that switches to a real page on click.

    The active page is rendered as a ``primary`` button so CSS can highlight it.
    Items marked ``"disabled": True`` are shown but not clickable.
    """
    if item.get("disabled"):
        st.button(
            item["title"],
            icon=f":material/{item['icon']}:",
            width="stretch",
            key=item["key"],
            disabled=True,
        )
        return

    active = current_title == item["title"]
    if st.button(
        item["title"],
        icon=f":material/{item['icon']}:",
        width="stretch",
        key=item["key"],
        type="primary" if active else "secondary",
    ):
        st.switch_page(pages[item["title"]])


def render_sidebar_nav(pages: dict, current_title: str) -> None:
    """Render the sidebar navigation: link-style items with Material icons
    and collapsible groups, styled to look borderless and clean.

    Clicking an item calls ``st.switch_page`` to load the matching page.
    Call ``apply_global_styles()`` before this, inside a ``with st.sidebar:``
    block. ``current_title`` (e.g. ``pg.title``) drives the active highlight.
    """
    with st.container(key="ca-nav"):
        for entry in NAV:
            if entry["kind"] == "item":
                _nav_link(pages, entry, current_title)
            elif entry["kind"] == "group":
                with st.expander(entry["title"], expanded=True):
                    if entry.get("badge"):
                        st.html(f'<span class="ca-soon">{entry["badge"]}</span>')
                    for item in entry["items"]:
                        _nav_link(pages, item, current_title)
            elif entry["kind"] == "divider":
                st.divider()


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

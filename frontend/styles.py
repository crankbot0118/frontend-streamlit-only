"""Reusable custom CSS for the Clone Automation dashboard.

Import and call ``apply_global_styles()`` once near the top of any page
(after ``st.set_page_config``) to get consistent styling across the app.
"""

import base64
import html
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

import streamlit as st

from datetime_local import (
    dt_html,
    emit_html,
    fmt_dt_fallback,
    fmt_relative_update_fallback,
    fmt_started_fallback,
    inject_local_datetime_js,
    refresh_html,
    relative_update_html,
    started_html,
)

BRAND_ORANGE = "#e87511"
BRAND_INK = "#131516"
BRAND_RED = "#cf222e"
BRAND_RED_BG = "rgba(207, 34, 46, 0.12)"
STATUS_ICON_PX = 18
SIDEBAR_WIDTH_PX = 200

# Repo root is the parent of the ``frontend/`` package that holds this file.
REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LOGO_PATH = REPO_ROOT / "assets" / "logo.svg"


@lru_cache(maxsize=None)
def _asset_data_uri(filename: str) -> str:
    """Read a file from ``assets/`` and return it as a base64 data URI."""
    path = REPO_ROOT / "assets" / filename
    try:
        data = path.read_bytes()
    except OSError:
        return ""
    b64 = base64.b64encode(data).decode("ascii")
    suffix = Path(filename).suffix.lower()
    mime = "image/svg+xml" if suffix == ".svg" else "image/png"
    return f"data:{mime};base64,{b64}"


def _nav_action_button_css(
    container_selector: str,
    *,
    accent: str,
    accent_bg: str,
    disabled_opacity: str = "0.55",
) -> str:
    """Compact nav-style Streamlit button (Trigger job, Abort, etc.)."""
    return f"""
  {container_selector} .stButton,
  {container_selector} .stDownloadButton {{
      width: auto !important;
      margin: 0 !important;
  }}

  {container_selector} .stButton button,
  {container_selector} .stDownloadButton button {{
      display: inline-flex !important;
      align-items: center !important;
      justify-content: flex-start !important;
      width: auto !important;
      min-height: 1.7rem !important;
      padding: 0.2rem 0.65rem !important;
      gap: 0.45rem !important;
      font-size: var(--ca-nav-font-size) !important;
      font-weight: 600 !important;
      line-height: 1.25 !important;
      border-radius: 5px !important;
      border: none !important;
      box-shadow: none !important;
      background: transparent !important;
      color: #9aa0a6 !important;
      cursor: not-allowed !important;
      opacity: {disabled_opacity} !important;
      white-space: nowrap !important;
  }}

  {container_selector} .stButton button p,
  {container_selector} .stDownloadButton button p {{
      margin: 0 !important;
      font-size: var(--ca-nav-font-size) !important;
      font-weight: 600 !important;
  }}

  {container_selector} .stButton button svg,
  {container_selector} .stButton button [data-testid="stIconMaterial"],
  {container_selector} .stDownloadButton button svg,
  {container_selector} .stDownloadButton button [data-testid="stIconMaterial"] {{
      width: 1rem !important;
      height: 1rem !important;
      font-size: 1rem !important;
      color: inherit !important;
      fill: currentColor !important;
  }}

  {container_selector} .stButton button:not(:disabled),
  {container_selector} .stDownloadButton button:not(:disabled) {{
      background: {accent_bg} !important;
      color: {accent} !important;
      cursor: pointer !important;
      opacity: 1 !important;
  }}

  {container_selector} .stButton button:not(:disabled) p,
  {container_selector} .stButton button:not(:disabled) svg,
  {container_selector} .stButton button:not(:disabled) [data-testid="stIconMaterial"],
  {container_selector} .stDownloadButton button:not(:disabled) p,
  {container_selector} .stDownloadButton button:not(:disabled) svg,
  {container_selector} .stDownloadButton button:not(:disabled) [data-testid="stIconMaterial"] {{
      color: {accent} !important;
      fill: {accent} !important;
  }}
"""


_GLOBAL_CSS = f"""
<style>
  /* Lock the shell to light mode (not system/dark) even if config.toml is
     not picked up from the repo root. */
  :root,
  .stApp {{
      color-scheme: light only;
      --primary-color: {BRAND_ORANGE};
      --background-color: #ffffff;
      --secondary-background-color: #f6f7f8;
      --text-color: {BRAND_INK};
      --ca-detail-inline-gap: 0.45rem;
      --ca-page-inset-top: 0.5rem;
      --ca-sidebar-inset-x: 0.5rem;
      --ca-main-inset-x: 1rem;
      --ca-main-inset-right: 1.25rem;
      --ca-header-row-height: 2rem;
      /* Type scale — all page text derives from the heading size. */
      --ca-title-size: 1.75rem;
      --ca-subtitle-size: calc(var(--ca-title-size) * 0.43);   /* ~0.75rem subtitle */
      --ca-body-size: calc(var(--ca-title-size) * 0.5);         /* ~0.875rem body */
      --ca-label-size: calc(var(--ca-title-size) * 0.486);        /* ~0.85rem labels */
      --ca-caption-size: calc(var(--ca-title-size) * 0.457);    /* ~0.8rem captions */
      --ca-run-meta-size: calc(var(--ca-title-size) * 0.4);     /* ~0.7rem card meta */
      --ca-nav-font-size: var(--ca-body-size);
      --ca-nav-item-gap: 0.18rem;
      --ca-nav-highlight-bg: rgba(232, 117, 17, 0.12);
      --ca-detail-meta-height: 1.6rem;
  }}
  [data-testid="stAppViewContainer"],
  .stApp,
  section.main {{
      background-color: #ffffff !important;
      color: {BRAND_INK} !important;
  }}
  [data-testid="stSidebar"],
  [data-testid="stSidebar"] > div {{
      background-color: #f6f7f8 !important;
  }}

  /* Sidebar shell: fixed width, full viewport height, no scroll bar. */
  [data-testid="stSidebar"] {{
      width: {SIDEBAR_WIDTH_PX}px !important;
      min-width: {SIDEBAR_WIDTH_PX}px !important;
      max-width: {SIDEBAR_WIDTH_PX}px !important;
      height: 100vh !important;
      max-height: 100vh !important;
      overflow: hidden !important;
  }}

  [data-testid="stSidebar"] > div,
  [data-testid="stSidebarContent"] {{
      height: 100% !important;
      max-height: 100vh !important;
      overflow-x: visible !important;
      overflow-y: hidden !important;
      -ms-overflow-style: none;
      scrollbar-width: none;
  }}

  [data-testid="stSidebar"] ::-webkit-scrollbar {{
      display: none;
  }}

  /* Hide the top-right toolbar (theme toggle + app menu with the
     Light/Dark/System theme picker) and the "Made with Streamlit" footer. */
  [data-testid="stToolbar"],
  [data-testid="stMainMenu"],
  [data-testid="stStatusWidget"],
  #MainMenu,
  footer {{
      display: none !important;
      visibility: hidden !important;
  }}

  /* Main content insets — modest gutter beside sidebar, still compact vertically. */
  section.main .block-container,
  section.main > .block-container,
  [data-testid="stMainBlockContainer"] {{
      padding-top: var(--ca-page-inset-top) !important;
      padding-bottom: 1.25rem !important;
      padding-left: var(--ca-main-inset-x) !important;
      padding-right: var(--ca-main-inset-right) !important;
      max-width: none !important;
  }}

  section.main .block-container [data-testid="stMainBlockContainer"] {{
      padding: 0 !important;
  }}

  [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] {{
      gap: 0.35rem !important;
  }}

  [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:first-child {{
      margin-top: 0 !important;
      padding-top: 0 !important;
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

  /* Collapse the empty sidebar header so content sits at the very top. */
  [data-testid="stSidebarHeader"] {{
      height: 0;
      min-height: 0;
      padding: 0;
  }}

  /* Sidebar content: flex column that fits the viewport without scrolling. */
  [data-testid="stSidebarUserContent"] {{
      display: flex;
      flex-direction: column;
      height: 100%;
      max-height: 100vh;
      min-height: 0;
      padding-top: var(--ca-page-inset-top);
      padding-left: var(--ca-sidebar-inset-x);
      padding-right: var(--ca-sidebar-inset-x);
      padding-bottom: 1.75rem;
      box-sizing: border-box;
      overflow: hidden;
  }}

  [data-testid="stSidebarUserContent"] > [data-testid="stVerticalBlock"] {{
      flex: 1 1 auto;
      min-height: 0;
      display: flex;
      flex-direction: column;
      gap: 0 !important;
  }}

  [data-testid="stSidebarUserContent"] [data-testid="stElementContainer"] {{
      margin-bottom: 0 !important;
      padding-bottom: 0 !important;
      padding-left: 0 !important;
      padding-right: 0 !important;
      max-width: 100% !important;
      box-sizing: border-box;
  }}

  [data-testid="stSidebarUserContent"] > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:first-child {{
      margin-top: 0 !important;
      padding-top: 0 !important;
  }}

  /* Logo — scale to sidebar content width; never clip or overflow. */
  .ca-logo {{
      margin: 0 0 0.35rem 0;
      padding: 0;
      flex: 0 0 auto;
      width: 100%;
      max-width: 100%;
      box-sizing: border-box;
      display: flex;
      align-items: center;
      overflow: visible;
  }}

  .ca-logo img {{
      width: 100%;
      max-width: 100%;
      height: auto;
      max-height: 2.35rem;
      object-fit: contain;
      object-position: left center;
      display: block;
  }}

  /* Page title block — same vertical slot as the logo. */
  .ca-page-header {{
      margin: 0;
      padding: 0;
  }}

  .ca-title {{
      display: flex;
      align-items: center;
      gap: 0.65rem;
      margin: 0;
      padding: 0;
      min-height: var(--ca-header-row-height);
      line-height: 1;
  }}

  .ca-title h1 {{
      margin: 0;
      padding: 0;
      font-size: var(--ca-title-size);
      font-weight: 700;
      letter-spacing: -0.02em;
      color: {BRAND_INK};
      line-height: 1;
  }}

  /* Accent bar under the title block. */
  .ca-title-rule {{
      height: 2px;
      width: 100%;
      border: none;
      margin: 0.04rem 0 0.06rem 0;
      border-radius: 999px;
      background: linear-gradient(90deg, {BRAND_ORANGE} 0%, rgba(232,117,17,0.15) 100%);
  }}

  .ca-subtitle {{
      margin: 0;
      padding: 0;
      color: #5b6166;
      font-size: var(--ca-subtitle-size);
      font-weight: 400;
      font-style: italic;
      line-height: 1.25;
      max-width: 52rem;
  }}

  /* ---------- Main content typography (body, captions, alerts) ---------- */
  [data-testid="stMainBlockContainer"] {{
      font-size: var(--ca-body-size);
      line-height: 1.5;
  }}

  [data-testid="stMainBlockContainer"] [data-testid="stMarkdownContainer"] p,
  [data-testid="stMainBlockContainer"] [data-testid="stMarkdownContainer"] li,
  [data-testid="stMainBlockContainer"] [data-testid="stText"] p,
  [data-testid="stMainBlockContainer"] .stMarkdown p,
  [data-testid="stMainBlockContainer"] .stMarkdown li {{
      font-size: var(--ca-body-size);
      line-height: 1.5;
      color: #3d4348;
  }}

  [data-testid="stMainBlockContainer"] [data-testid="stCaptionContainer"],
  [data-testid="stMainBlockContainer"] [data-testid="stCaptionContainer"] p,
  [data-testid="stMainBlockContainer"] [data-testid="stCaptionContainer"] small,
  [data-testid="stMainBlockContainer"] .stCaption {{
      font-size: var(--ca-caption-size) !important;
      line-height: 1.4;
      color: #6b7177 !important;
  }}

  [data-testid="stMainBlockContainer"] [data-testid="stAlert"] p,
  [data-testid="stMainBlockContainer"] [data-testid="stAlert"] [data-testid="stMarkdownContainer"] p,
  [data-testid="stMainBlockContainer"] [data-testid="stNotification"] p {{
      font-size: var(--ca-body-size);
      line-height: 1.45;
  }}

  [data-testid="stMainBlockContainer"] [data-testid="stWidgetLabel"] p,
  [data-testid="stMainBlockContainer"] [data-testid="stWidgetLabel"] span {{
      font-size: var(--ca-label-size) !important;
      line-height: 1.35;
  }}

  /* ---------- Sidebar navigation ---------- */

  .st-key-ca-nav {{
      --ca-nav-x: 0.75rem;
      --ca-nav-icon: 1rem;
      --ca-nav-gap: 0.45rem;
      --ca-nav-text: calc(var(--ca-nav-icon) + var(--ca-nav-gap));
      flex: 1 1 auto;
      min-height: 0;
      overflow: hidden;
      width: 100%;
      max-width: 100%;
      box-sizing: border-box;
  }}

  /* Consistent vertical gap between every nav row (Home, groups, Execute Clone, etc.). */
  .st-key-ca-nav > [data-testid="stVerticalBlock"] {{
      gap: var(--ca-nav-item-gap) !important;
      align-items: stretch;
  }}

  .st-key-ca-nav [data-testid="stElementContainer"] {{
      align-items: flex-start;
      text-align: left;
      margin: 0 !important;
      padding: 0 !important;
      width: 100% !important;
      max-width: 100% !important;
      box-sizing: border-box;
  }}

  .st-key-ca-nav .stButton {{
      margin: 0 !important;
  }}

  .st-key-ca-nav [data-testid="stExpanderDetails"] [data-testid="stVerticalBlock"] {{
      gap: var(--ca-nav-item-gap) !important;
  }}

  /* Borderless, left-aligned link-style nav buttons (descendant selectors so
     we catch the button regardless of intermediate wrappers). */
  .st-key-ca-nav .stButton button {{
      display: flex !important;
      align-items: center !important;
      justify-content: flex-start !important;
      text-align: left !important;
      width: 100% !important;
      min-height: 1.7rem !important;
      background: transparent !important;
      border: none !important;
      box-shadow: none !important;
      outline: none !important;
      gap: var(--ca-nav-gap) !important;
      padding: 0.24rem var(--ca-nav-x) 0.24rem var(--ca-nav-x) !important;
      border-radius: 5px;
      color: {BRAND_INK};
  }}

  .st-key-ca-nav .stButton button svg,
  .st-key-ca-nav .stButton button [data-testid="stIconMaterial"] {{
      flex: 0 0 var(--ca-nav-icon) !important;
      width: var(--ca-nav-icon) !important;
      height: var(--ca-nav-icon) !important;
      margin: 0 !important;
      align-self: center !important;
      display: inline-flex !important;
      align-items: center !important;
      justify-content: center !important;
  }}

  /* Stop Streamlit from centering the label inside the button. */
  .st-key-ca-nav .stButton button > div,
  .st-key-ca-nav .stButton button [data-testid="stMarkdownContainer"] {{
      width: auto;
      flex: 1 1 auto;
      display: flex !important;
      justify-content: flex-start !important;
      text-align: left !important;
  }}

  .st-key-ca-nav .stButton button p {{
      margin: 0;
      font-weight: 600;
      font-size: var(--ca-nav-font-size);
      text-align: left !important;
      line-height: 1;
      align-self: center !important;
  }}

  .st-key-ca-nav .stButton button:hover {{
      background: var(--ca-nav-highlight-bg) !important;
      color: {BRAND_ORANGE};
  }}

  .st-key-ca-nav .stButton button:hover svg,
  .st-key-ca-nav .stButton button:hover p {{
      color: {BRAND_ORANGE};
  }}

  /* Active item — same look as hover (no left accent bar). */
  .st-key-ca-nav .stButton button[kind="primary"] {{
      background: var(--ca-nav-highlight-bg) !important;
      box-shadow: none !important;
      color: {BRAND_ORANGE} !important;
  }}

  .st-key-ca-nav .stButton button[kind="primary"] p {{
      color: {BRAND_ORANGE} !important;
      font-weight: 600;
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

  /* Small yellow "Coming soon!" highlight — aligned with nav labels. */
  .ca-soon {{
      display: inline-block;
      margin: 0 0 0.18rem var(--ca-nav-text);
      padding: 0.04rem 0.32rem;
      border-radius: 4px;
      background: #fff3cd;
      color: #8a6500;
      font-size: 0.62rem;
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
      gap: var(--ca-nav-gap) !important;
      min-height: 1.7rem !important;
      padding: 0.24rem var(--ca-nav-x) 0.24rem var(--ca-nav-x) !important;
      font-weight: 600;
      text-transform: none;
      letter-spacing: normal;
      font-size: var(--ca-nav-font-size);
      color: #5b6166;
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

  /* Chevron in the same column as nav icons. */
  .st-key-ca-nav [data-testid="stExpander"] summary svg {{
      order: -1;
      flex: 0 0 var(--ca-nav-icon) !important;
      width: var(--ca-nav-icon) !important;
      height: var(--ca-nav-icon) !important;
      margin: 0 !important;
      color: {BRAND_ORANGE};
      fill: {BRAND_ORANGE};
  }}

  /* Left-align the summary label text too. */
  .st-key-ca-nav [data-testid="stExpander"] summary p,
  .st-key-ca-nav [data-testid="stExpander"] summary span {{
      flex: 1 1 auto;
      text-align: left !important;
      line-height: 1.25;
      font-size: var(--ca-nav-font-size);
      font-weight: 600;
  }}

  /* Group items use the same left edge as top-level nav rows. */
  .st-key-ca-nav [data-testid="stExpanderDetails"] {{
      padding-left: 0 !important;
      padding-top: 0;
      padding-bottom: 0;
      border: none !important;
      box-shadow: none !important;
  }}

  /* Remove the expander's own trailing space before the divider. */
  .st-key-ca-nav [data-testid="stExpander"] {{
      margin-bottom: 0 !important;
  }}

  /* Thin black divider line before Execute Clone. */
  .ca-nav-divider-line {{
      display: block;
      height: 1px;
      border: none;
      margin: var(--ca-nav-item-gap) var(--ca-nav-x) var(--ca-nav-item-gap) var(--ca-nav-x);
      background: {BRAND_INK};
  }}

  /* ---------- Run History filters + Execute Clone form ---------- */
  .st-key-ca-run-filters,
  .st-key-ca-execute-clone-form {{
      margin-top: -0.08rem !important;
      margin-bottom: 0.32rem !important;
  }}
  .st-key-ca-run-filters [data-testid="stVerticalBlock"],
  .st-key-ca-execute-clone-form [data-testid="stVerticalBlock"] {{
      gap: 0.12rem !important;
  }}
  .st-key-ca-run-filters [data-testid="stHorizontalBlock"],
  .st-key-ca-execute-clone-form [data-testid="stHorizontalBlock"] {{
      align-items: flex-end;
      gap: 0.65rem;
  }}
  .st-key-ca-run-filters [data-testid="stWidgetLabel"] p,
  .st-key-ca-execute-clone-form [data-testid="stWidgetLabel"] p {{
      color: #6b7177 !important;
      font-size: var(--ca-label-size);
      font-weight: 600;
  }}
  /* Force white filter controls (select + date) on light background. */
  .st-key-ca-run-filters [data-testid="stSelectbox"] > div > div,
  .st-key-ca-run-filters [data-testid="stSelectbox"] [data-baseweb="select"] > div,
  .st-key-ca-run-filters [data-testid="stDateInput"] > div > div,
  .st-key-ca-run-filters [data-testid="stDateInput"] [data-baseweb="input"],
  .st-key-ca-run-filters [data-testid="stDateInput"] input,
  .st-key-ca-execute-clone-form [data-testid="stSelectbox"] > div > div,
  .st-key-ca-execute-clone-form [data-testid="stSelectbox"] [data-baseweb="select"] > div {{
      background-color: #ffffff !important;
      color: {BRAND_INK} !important;
      border-color: #e3e6e8 !important;
  }}
  .st-key-ca-run-filters [data-testid="stSelectbox"] svg,
  .st-key-ca-run-filters [data-testid="stDateInput"] svg,
  .st-key-ca-execute-clone-form [data-testid="stSelectbox"] svg {{
      color: #6b7177 !important;
      fill: #6b7177 !important;
  }}

  /* Open select control — same peach highlight as sidebar nav active item. */
  .st-key-ca-run-filters [data-testid="stSelectbox"] [data-baseweb="select"]:focus-within > div,
  .st-key-ca-run-filters [data-testid="stSelectbox"] [data-baseweb="select"] > div[aria-expanded="true"],
  .st-key-ca-execute-clone-form [data-testid="stSelectbox"] [data-baseweb="select"]:focus-within > div,
  .st-key-ca-execute-clone-form [data-testid="stSelectbox"] [data-baseweb="select"] > div[aria-expanded="true"] {{
      background-color: var(--ca-nav-highlight-bg) !important;
      border-color: rgba(232, 117, 17, 0.35) !important;
      color: {BRAND_ORANGE} !important;
  }}
  .st-key-ca-run-filters [data-testid="stSelectbox"] [data-baseweb="select"]:focus-within svg,
  .st-key-ca-run-filters [data-testid="stSelectbox"] [data-baseweb="select"] > div[aria-expanded="true"] svg,
  .st-key-ca-execute-clone-form [data-testid="stSelectbox"] [data-baseweb="select"]:focus-within svg,
  .st-key-ca-execute-clone-form [data-testid="stSelectbox"] [data-baseweb="select"] > div[aria-expanded="true"] svg {{
      color: {BRAND_ORANGE} !important;
      fill: {BRAND_ORANGE} !important;
  }}

  /* Dropdown list — hover / keyboard focus / selected option. */
  div[data-baseweb="popover"] [role="listbox"] [role="option"]:hover,
  div[data-baseweb="popover"] [role="listbox"] [role="option"][aria-selected="true"],
  div[data-baseweb="popover"] [role="listbox"] [role="option"][data-highlighted="true"],
  div[data-baseweb="popover"] [role="listbox"] li[data-highlighted="true"] {{
      background-color: var(--ca-nav-highlight-bg) !important;
      color: {BRAND_ORANGE} !important;
  }}
  div[data-baseweb="popover"] [role="listbox"] [role="option"] {{
      color: {BRAND_INK} !important;
      border-radius: 5px !important;
  }}

  /* Execute Clone — reserve space; Trigger job fixed to viewport bottom-right. */
  .st-key-ca-execute-clone-page,
  .st-key-ca-execute-clone-page > [data-testid="stVerticalBlock"],
  .st-key-ca-execute-clone-page > [data-testid="stVerticalBlockBorderWrapper"] {{
      width: 100% !important;
      margin: 0 !important;
      padding: 0 0 3.5rem 0 !important;
  }}
  .st-key-ca-execute-clone-page > [data-testid="stVerticalBlock"] {{
      gap: 0.25rem !important;
  }}
  .st-key-ca-execute-clone-page > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:has(.st-key-ca-execute-clone-actions),
  .st-key-ca-execute-clone-actions {{
      position: fixed !important;
      right: var(--ca-main-inset-right) !important;
      bottom: 1rem !important;
      left: auto !important;
      top: auto !important;
      width: auto !important;
      height: auto !important;
      margin: 0 !important;
      padding: 0 !important;
      z-index: 120;
      pointer-events: none;
  }}
  .st-key-ca-execute-clone-actions [data-testid="stVerticalBlock"],
  .st-key-ca-execute-clone-actions [data-testid="stVerticalBlockBorderWrapper"],
  .st-key-ca-execute-clone-actions [data-testid="stElementContainer"] {{
      width: auto !important;
      margin: 0 !important;
      padding: 0 !important;
      pointer-events: auto;
  }}
  .st-key-ca-execute-clone-actions [data-testid="stVerticalBlock"],
  .st-key-ca-execute-clone-actions [data-testid="stVerticalBlockBorderWrapper"] {{
      display: flex !important;
      flex-direction: row !important;
      justify-content: flex-end !important;
      align-items: center !important;
  }}
  {_nav_action_button_css(
      ".st-key-ca-execute-clone-actions",
      accent=BRAND_RED,
      accent_bg=BRAND_RED_BG,
  )}

  .ca-exec-ready {{
      margin: 0.35rem 0 0.15rem 0;
      font-size: var(--ca-body-size);
      line-height: 1.5;
      color: #5b6166;
  }}

  .ca-exec-ready strong {{
      color: {BRAND_INK};
      font-weight: 700;
  }}

  /* ---------- Sidebar bottom status (fixed to viewport) ---------- */

  /* Anchor to the bottom of the screen, not the nav stack. */
  [data-testid="stSidebarUserContent"] > [data-testid="stVerticalBlock"] > .st-key-ca-status,
  .st-key-ca-status {{
      position: fixed !important;
      left: 0 !important;
      bottom: 0.45rem !important;
      width: {SIDEBAR_WIDTH_PX}px !important;
      z-index: 1000;
      margin: 0 !important;
      padding: 0.35rem var(--ca-sidebar-inset-x) 0.45rem var(--ca-sidebar-inset-x) !important;
      box-sizing: border-box;
      height: auto !important;
      flex: 0 0 auto !important;
      overflow: visible !important;
      display: flex !important;
      justify-content: center !important;
      align-items: center !important;
      background: linear-gradient(
          180deg,
          rgba(246, 247, 248, 0) 0%,
          rgba(246, 247, 248, 0.92) 35%,
          #f6f7f8 100%
      );
  }}

  .st-key-ca-status [data-testid="stElementContainer"],
  .st-key-ca-status [data-testid="stVerticalBlock"] {{
      margin: 0 !important;
      padding: 0 !important;
      width: 100% !important;
  }}

  /* Single inline row: dot + compact last-refresh text. */
  .ca-status {{
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.35rem;
      width: 100%;
      max-width: 100%;
      white-space: nowrap;
      line-height: 1;
      padding: 0;
      overflow: visible;
  }}

  .ca-status .ca-dot-wrap {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      flex: 0 0 auto;
      width: 14px;
      height: 14px;
      overflow: visible;
  }}

  .ca-status .ca-dot {{
      width: 7px;
      height: 7px;
      border-radius: 50%;
      flex: 0 0 auto;
  }}

  .ca-status .ca-refresh-text {{
      font-size: 0.56rem;
      color: #6b7177;
      line-height: 1.1;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      flex: 0 1 auto;
      min-width: 0;
  }}

  /* Live: glowing green with a pulse. */
  .ca-status.is-live .ca-dot {{
      background: #22c55e;
      animation: ca-pulse 1.6s ease-out infinite;
  }}

  /* Offline: red with a steady glow. */
  .ca-status.is-offline .ca-dot {{
      background: #ef4444;
      box-shadow: 0 0 7px 1px rgba(239, 68, 68, 0.7);
  }}

  @keyframes ca-pulse {{
      0%   {{ box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.55); }}
      70%  {{ box-shadow: 0 0 0 6px rgba(34, 197, 94, 0); }}
      100% {{ box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }}
  }}

  /* ---------- Status badges (reused on cards + steps) ---------- */
  .ca-badge {{
      display: inline-block;
      padding: 0.06rem 0.45rem;
      border-radius: 999px;
      font-size: calc(var(--ca-caption-size) * 0.92);
      font-weight: 700;
      letter-spacing: 0.02em;
      white-space: nowrap;
  }}
  .ca-badge.green  {{ background: #dafbe1; color: #116329; }}
  .ca-badge.blue   {{ background: #ddf4ff; color: #0a3069; }}
  .ca-badge.gray   {{ background: #eef0f2; color: #57606a; }}
  .ca-badge.red    {{ background: #ffebe9; color: #cf222e; }}
  .ca-badge.orange {{ background: #fff1e5; color: #bc4c00; }}
  .ca-badge.violet {{ background: #fbefff; color: #6639ba; }}

  /* ---------- Run cards (Run History) ---------- */
  .st-key-ca-runs {{
      --ca-run-card-gap: 0.08rem;
      --ca-run-card-pad-y: 0.28rem;
      --ca-run-card-pad-x: 0.65rem;
      --ca-run-card-pad-right: 0.45rem;
      --ca-run-card-line: 1.65rem;
      --ca-run-inline-gap: 0.28rem;
      margin-top: 0.18rem !important;
  }}
  .st-key-ca-runs > [data-testid="stVerticalBlock"],
  .st-key-ca-runs > [data-testid="stVerticalBlockBorderWrapper"] > [data-testid="stVerticalBlock"],
  .st-key-ca-runs [data-testid="stVerticalBlock"]:has(> [class*="st-key-runcard_"]) {{
      gap: var(--ca-run-card-gap) !important;
      align-items: stretch !important;
      margin: 0 !important;
      padding: 0 !important;
  }}

  /* Card shell — compact single-line row. */
  [class*="st-key-runcard_"] {{
      position: relative;
      border: 1px solid #e3e6e8;
      border-radius: 6px;
      padding: var(--ca-run-card-pad-y) var(--ca-run-card-pad-right) var(--ca-run-card-pad-y) var(--ca-run-card-pad-x) !important;
      margin: 0 !important;
      background: #ffffff;
      transition: border-color 0.15s ease, box-shadow 0.15s ease;
      display: block !important;
      box-sizing: border-box;
      min-height: 0 !important;
      overflow: hidden !important;
  }}
  [class*="st-key-runcard_"] > [data-testid="stVerticalBlock"],
  [class*="st-key-runcard_"] > [data-testid="stVerticalBlockBorderWrapper"] > [data-testid="stVerticalBlock"] {{
      gap: 0 !important;
      margin: 0 !important;
      padding: 0 !important;
      position: relative !important;
      min-height: 0 !important;
      height: auto !important;
  }}
  [class*="st-key-runcard_"] [data-testid="stHorizontalBlock"] {{
      display: flex !important;
      flex-direction: row !important;
      flex-wrap: nowrap !important;
      align-items: center !important;
      width: 100% !important;
      margin: 0 !important;
      padding: 0 !important;
      gap: 0.25rem !important;
      min-height: var(--ca-run-card-line) !important;
  }}
  [class*="st-key-runcard_"] [data-testid="column"] {{
      display: flex !important;
      align-items: center !important;
      justify-content: flex-start !important;
      min-height: var(--ca-run-card-line) !important;
      padding-top: 0 !important;
      padding-bottom: 0 !important;
      margin: 0 !important;
  }}
  [class*="st-key-runcard_"] [data-testid="column"]:first-child {{
      flex: 1 1 auto !important;
      min-width: 0 !important;
      width: auto !important;
      overflow: hidden !important;
  }}
  [class*="st-key-runcard_"] [data-testid="column"]:last-child {{
      flex: 0 0 auto !important;
      width: auto !important;
      min-width: 1.75rem !important;
      max-width: 2rem !important;
      justify-content: center !important;
      position: relative !important;
      z-index: 2 !important;
  }}
  [class*="st-key-runcard_"] [data-testid="column"]:first-child [data-testid="stVerticalBlock"],
  [class*="st-key-runcard_"] [data-testid="column"]:first-child [data-testid="stElementContainer"] {{
      margin: 0 !important;
      padding: 0 !important;
      min-height: 0 !important;
      width: 100% !important;
      max-width: 100% !important;
      overflow: hidden !important;
  }}
  [class*="st-key-runcard_"] [data-testid="column"]:last-child [data-testid="stVerticalBlock"],
  [class*="st-key-runcard_"] [data-testid="column"]:last-child [data-testid="stElementContainer"] {{
      margin: 0 !important;
      padding: 0 !important;
      min-height: 0 !important;
      width: auto !important;
      justify-content: center !important;
  }}
  [class*="st-key-runcard_"] > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"],
  [class*="st-key-runcard_"] > [data-testid="stVerticalBlockBorderWrapper"] > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"] {{
      margin: 0 !important;
      padding: 0 !important;
      min-height: 0 !important;
  }}
  [class*="st-key-runcard_"] > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:first-child,
  [class*="st-key-runcard_"] > [data-testid="stVerticalBlockBorderWrapper"] > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:first-child {{
      width: 100% !important;
      min-width: 0 !important;
      min-height: 0 !important;
  }}
  [class*="st-key-runcard_"] [data-testid="stMarkdownContainer"],
  [class*="st-key-runcard_"] [data-testid="stMarkdownContainer"] p {{
      margin: 0 !important;
      padding: 0 !important;
      line-height: 1.2 !important;
  }}
  [class*="st-key-runcard_"] [data-testid="stElementContainer"]:has([data-testid="stHtml"]) {{
      margin: 0 !important;
      padding: 0 !important;
      min-height: 0 !important;
      max-height: var(--ca-run-card-line) !important;
      height: var(--ca-run-card-line) !important;
      line-height: 0 !important;
      flex: 0 0 auto !important;
      overflow: hidden !important;
  }}
  [class*="st-key-runcard_"] [data-testid="stHtml"] {{
      display: block !important;
      margin: 0 !important;
      padding: 0 !important;
      line-height: 0 !important;
      max-height: var(--ca-run-card-line) !important;
      height: var(--ca-run-card-line) !important;
      overflow: hidden !important;
  }}
  [class*="st-key-runcard_"] [data-testid="stHtml"] iframe {{
      display: block !important;
      width: 100% !important;
      margin: 0 !important;
      padding: 0 !important;
      border: none !important;
      background: transparent !important;
      min-height: var(--ca-run-card-line) !important;
      max-height: var(--ca-run-card-line) !important;
      height: var(--ca-run-card-line) !important;
      overflow: hidden !important;
  }}
  [class*="st-key-runcard_"]:hover {{
      border-color: {BRAND_ORANGE};
      box-shadow: 0 1px 8px rgba(19, 21, 22, 0.06);
  }}

  /* Redirect arrow — icon-only tertiary button in the right column. */
  [class*="st-key-runcard_"] [class*="st-key-open_run_"],
  [class*="st-key-runcard_"] [data-testid="column"]:last-child [data-testid="stElementContainer"]:has(.stButton) {{
      position: relative !important;
      z-index: 3 !important;
      width: auto !important;
      height: auto !important;
      margin: 0 !important;
      padding: 0 !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      overflow: visible !important;
  }}
  [class*="st-key-runcard_"] [class*="st-key-open_run_"] .stButton,
  [class*="st-key-runcard_"] [data-testid="column"]:last-child .stButton {{
      width: auto !important;
      margin: 0 !important;
      min-height: 0 !important;
      display: flex !important;
      align-items: center !important;
  }}
  [class*="st-key-runcard_"] [class*="st-key-open_run_"] .stButton button,
  [class*="st-key-runcard_"] [data-testid="column"]:last-child .stButton button {{
      width: auto !important;
      min-width: 1.65rem !important;
      min-height: var(--ca-run-card-line) !important;
      height: var(--ca-run-card-line) !important;
      background: transparent !important;
      background-color: transparent !important;
      border: none !important;
      box-shadow: none !important;
      color: #8a9097 !important;
      padding: 0 !important;
      gap: 0 !important;
      display: inline-flex !important;
      align-items: center !important;
      justify-content: center !important;
  }}
  [class*="st-key-runcard_"] [class*="st-key-open_run_"] .stButton button [data-testid="stMarkdownContainer"],
  [class*="st-key-runcard_"] [data-testid="column"]:last-child .stButton button [data-testid="stMarkdownContainer"] {{
      display: none !important;
      width: 0 !important;
      min-width: 0 !important;
      max-width: 0 !important;
      margin: 0 !important;
      padding: 0 !important;
      overflow: hidden !important;
  }}
  [class*="st-key-runcard_"] [class*="st-key-open_run_"] .stButton button [data-testid="stIconMaterial"],
  [class*="st-key-runcard_"] [data-testid="column"]:last-child .stButton button [data-testid="stIconMaterial"] {{
      font-size: 1.2rem !important;
      width: 1.2rem !important;
      height: 1.2rem !important;
      line-height: 1 !important;
      color: #8a9097 !important;
      flex: 0 0 auto !important;
  }}
  [class*="st-key-runcard_"] [class*="st-key-open_run_"] .stButton button svg,
  [class*="st-key-runcard_"] [data-testid="column"]:last-child .stButton button svg {{
      width: 1.2rem !important;
      height: 1.2rem !important;
      color: #8a9097 !important;
      fill: currentColor !important;
  }}
  [class*="st-key-runcard_"] [class*="st-key-open_run_"] .stButton button:hover,
  [class*="st-key-runcard_"] [data-testid="column"]:last-child .stButton button:hover {{
      background: transparent !important;
      background-color: transparent !important;
      color: {BRAND_ORANGE} !important;
  }}
  [class*="st-key-runcard_"] [class*="st-key-open_run_"] .stButton button:hover svg,
  [class*="st-key-runcard_"] [class*="st-key-open_run_"] .stButton button:hover [data-testid="stIconMaterial"],
  [class*="st-key-runcard_"] [data-testid="column"]:last-child .stButton button:hover svg,
  [class*="st-key-runcard_"] [data-testid="column"]:last-child .stButton button:hover [data-testid="stIconMaterial"] {{
      color: {BRAND_ORANGE} !important;
      fill: {BRAND_ORANGE} !important;
  }}

  .ca-run {{
      margin: 0;
      padding: 0;
      line-height: 1.25;
      width: 100%;
  }}
  .ca-run-oneline {{
      display: flex;
      flex-wrap: nowrap;
      align-items: center;
      justify-content: flex-start;
      gap: var(--ca-run-inline-gap);
      width: 100%;
      box-sizing: border-box;
      font-size: var(--ca-body-size);
      font-weight: 600;
      color: {BRAND_INK};
      line-height: 1.25;
      min-width: 0;
      min-height: var(--ca-run-card-line);
  }}
  .ca-run-oneline .ca-run-primary {{
      display: inline-flex;
      align-items: center;
      gap: var(--ca-run-inline-gap);
      flex: 1 1 auto;
      min-width: 0;
      overflow: hidden;
  }}
  .ca-run-oneline .ca-run-primary > span:not(.sep),
  .ca-run-oneline .ca-run-primary .ca-badge {{
      flex-shrink: 0;
      white-space: nowrap;
  }}
  .ca-run-oneline .sep {{
      color: #c2c7cc;
      font-weight: 400;
      flex-shrink: 0;
      user-select: none;
  }}
  .ca-run-oneline .ca-run-client {{
      font-weight: 700;
      flex-shrink: 0;
  }}
  .ca-run-oneline .arrow {{
      color: {BRAND_ORANGE};
      margin: 0 0.12rem;
  }}
  .ca-run-oneline .ca-run-primary .ca-badge {{
      padding: 0.04rem 0.34rem;
      font-size: calc(var(--ca-caption-size) * 0.88);
      line-height: 1.15;
  }}
  .ca-run-oneline .ca-run-meta-part {{
      margin-left: auto;
      display: flex;
      align-items: center;
      gap: 12px;
      min-width: 420px;
      justify-content: flex-end;
      flex: 0 0 auto;
      box-sizing: border-box;
      padding-right: 0.12rem;
      font-size: var(--ca-run-meta-size);
      font-weight: 400;
      font-style: italic;
      color: #7a8086;
      white-space: nowrap;
  }}
  .ca-run-oneline .ca-run-meta-part .sep {{
      font-style: normal;
  }}
  .ca-run-oneline .ca-run-meta-part .ca-run-metaline {{
      display: inline-flex;
      align-items: center;
      gap: 0.12rem;
      white-space: nowrap;
      flex-shrink: 0;
  }}
  .ca-run-oneline .ca-run-meta-part .mi {{
      font-style: normal;
      font-size: 0.88em;
      line-height: 1;
  }}
  .ca-run-metaline {{
      display: inline-flex;
      align-items: center;
      gap: 0.22rem;
  }}
  .ca-run-metaline .mi {{
      font-size: 0.92rem;
      line-height: 1;
  }}
  .ca-run-metaline .mi-start {{ color: #1a7f37; }}
  .ca-run-metaline .mi-upd   {{ color: {BRAND_ORANGE}; }}
  .ca-run-metaline .mi-dur   {{ color: #8a9097; }}

  /* ---------- Run details header ---------- */
  .st-key-ca-detail-header {{
      --ca-detail-inline-gap: 0.28rem;
      --ca-detail-title-height: 1.38rem;
      --ca-detail-meta-height: 1.05rem;
  }}
  .ca-run-sep {{ color: #c2c7cc; font-weight: 400; }}
  /* Title parts use the same gap as the middot-separated heading text. */
  .ca-detail-title-parts {{
      display: inline-flex;
      align-items: center;
      gap: var(--ca-detail-inline-gap);
      margin: 0;
      padding: 0;
      font-size: var(--ca-title-size);
      font-weight: 700;
      letter-spacing: -0.02em;
      color: {BRAND_INK};
      line-height: 1;
      white-space: nowrap;
      width: fit-content;
      max-width: none;
  }}
  .ca-detail-page-header {{
      margin: 0;
      padding: 0;
      display: inline-block;
      width: fit-content;
      max-width: none;
      vertical-align: middle;
  }}
  .ca-detail-page-header .ca-title {{
      display: inline-flex;
      align-items: center;
      min-height: 0;
      margin: 0;
      padding: 0;
  }}
  .ca-detail-title-parts .ca-run-sep {{
      flex: 0 0 auto;
      font-weight: 400;
  }}
  .ca-detail-title-parts .arrow {{
      color: {BRAND_ORANGE};
  }}
  /* Title row: Run # heading then Abort — single inline flex row, no overlap. */
  .st-key-ca-detail-title-row,
  .st-key-ca-detail-title-row [data-testid="stVerticalBlock"],
  .st-key-ca-detail-title-row [data-testid="stVerticalBlockBorderWrapper"] {{
      display: flex !important;
      flex-direction: row !important;
      align-items: center !important;
      flex-wrap: nowrap !important;
      gap: var(--ca-detail-inline-gap) !important;
      width: fit-content !important;
      max-width: 100% !important;
      min-height: 0 !important;
      height: auto !important;
      margin: 0 !important;
      padding: 0 !important;
  }}
  .st-key-ca-detail-title-row [data-testid="stElementContainer"] {{
      flex: 0 0 auto !important;
      width: auto !important;
      min-width: 0 !important;
      max-width: none !important;
      margin: 0 !important;
      padding: 0 !important;
      position: relative !important;
  }}
  .st-key-ca-detail-title-row [data-testid="stHtml"],
  .st-key-ca-detail-title-row [data-testid="stHtml"] iframe,
  .st-key-ca-detail-title-row .stHtml {{
      width: auto !important;
      max-width: none !important;
      min-width: 0 !important;
      height: auto !important;
      display: block !important;
      overflow: visible !important;
  }}
  .st-key-ca-detail-title-row [data-testid="stElementContainer"]:has([data-testid="stHtml"]) {{
      flex: 0 0 auto !important;
      width: fit-content !important;
      max-width: none !important;
      overflow: visible !important;
  }}
  .st-key-detail-actions,
  .st-key-detail-actions [data-testid="stVerticalBlock"],
  .st-key-detail-actions [data-testid="stVerticalBlockBorderWrapper"] {{
      display: flex !important;
      flex-direction: row !important;
      align-items: center !important;
      flex-wrap: nowrap !important;
      gap: 0 !important;
      width: auto !important;
      margin: 0 !important;
      flex: 0 0 auto !important;
      flex-shrink: 0 !important;
  }}
  .st-key-detail-actions [data-testid="stElementContainer"] {{
      display: inline-flex !important;
      flex-direction: row !important;
      align-items: center !important;
      width: auto !important;
      flex: 0 0 auto !important;
      margin: 0 !important;
      padding: 0 !important;
  }}
  .st-key-ca-detail-title-row .st-key-detail_abort .stButton button,
  .st-key-ca-detail-title-row .st-key-detail_abort .stDownloadButton button {{
      min-height: calc(var(--ca-detail-title-height) - 0.2rem) !important;
      height: calc(var(--ca-detail-title-height) - 0.2rem) !important;
      padding: 0 0.42rem !important;
      gap: 0.28rem !important;
      line-height: 1 !important;
      font-size: calc(var(--ca-nav-font-size) * 0.92) !important;
  }}
  {_nav_action_button_css(
      ".st-key-detail_abort",
      accent=BRAND_RED,
      accent_bg=BRAND_RED_BG,
  )}
  /* Meta row: strict single horizontal line. */
  .st-key-ca-detail-meta-row {{
      width: 100%;
      margin: -0.42rem 0 -0.22rem 0 !important;
      padding: 0 !important;
      min-height: 0 !important;
  }}
  .st-key-ca-detail-meta-row [data-testid="stHorizontalBlock"] {{
      display: flex !important;
      flex-direction: row !important;
      align-items: center !important;
      flex-wrap: nowrap !important;
      width: 100% !important;
      margin: 0 !important;
      padding: 0 !important;
      gap: 0.28rem !important;
      min-height: var(--ca-detail-meta-height) !important;
  }}
  .st-key-ca-detail-meta-row [data-testid="column"] {{
      display: flex !important;
      align-items: center !important;
      justify-content: flex-start !important;
      min-height: var(--ca-detail-meta-height) !important;
      padding-top: 0 !important;
      padding-bottom: 0 !important;
  }}
  .st-key-ca-detail-meta-row [data-testid="column"]:last-child {{
      justify-content: flex-end !important;
  }}
  .st-key-ca-detail-meta-row [data-testid="column"] [data-testid="stVerticalBlock"],
  .st-key-ca-detail-meta-row [data-testid="column"] [data-testid="stElementContainer"] {{
      display: flex !important;
      align-items: center !important;
      justify-content: inherit !important;
      margin: 0 !important;
      padding: 0 !important;
      min-height: 0 !important;
  }}
  .st-key-ca-detail-meta-row [data-testid="column"]:first-child [data-testid="stElementContainer"],
  .st-key-ca-detail-meta-row [data-testid="column"]:first-child iframe {{
      display: flex !important;
      align-items: center !important;
      width: 100% !important;
      min-height: var(--ca-detail-meta-height) !important;
      margin: 0 !important;
      padding: 0 !important;
  }}
  .st-key-ca-detail-meta-row .st-key-detail-refresh,
  .st-key-ca-detail-meta-row .st-key-detail-download-log {{
      width: auto !important;
      margin: 0 !important;
      padding: 0 !important;
  }}
  .st-key-detail-download-log [data-testid="stElementContainer"],
  .st-key-detail-download-log [data-testid="stVerticalBlock"] {{
      width: auto !important;
      margin: 0 !important;
      padding: 0 !important;
  }}
  .st-key-detail-download-log .stDownloadButton,
  .st-key-detail-download-log .stDownloadButton button {{
      width: auto !important;
      min-height: var(--ca-detail-meta-height) !important;
      height: var(--ca-detail-meta-height) !important;
      margin: 0 !important;
      padding: 0 !important;
      background: transparent !important;
      border: none !important;
      box-shadow: none !important;
      color: {BRAND_ORANGE} !important;
      font-size: var(--ca-run-meta-size) !important;
      font-weight: 600 !important;
      line-height: 1 !important;
      display: inline-flex !important;
      align-items: center !important;
  }}
  .st-key-detail-download-log .stDownloadButton button:hover {{
      text-decoration: underline;
      color: {BRAND_ORANGE} !important;
  }}
  .st-key-ca-detail-meta-row .st-key-detail-refresh [data-testid="stVerticalBlock"],
  .st-key-ca-detail-meta-row .st-key-detail-refresh [data-testid="stElementContainer"] {{
      display: flex !important;
      flex-direction: row !important;
      align-items: center !important;
      justify-content: flex-end !important;
      width: auto !important;
      margin: 0 !important;
      gap: 0.22rem !important;
      min-height: var(--ca-detail-meta-height) !important;
  }}
  .st-key-detail-refresh [data-testid="stWidgetLabel"],
  .st-key-detail-refresh [data-testid="stWidgetLabel"] p,
  .st-key-detail-refresh [data-testid="stWidgetLabel"] span,
  .st-key-detail-refresh [data-testid="stMarkdownContainer"] p,
  .st-key-detail-refresh label,
  .st-key-detail-refresh label p,
  .st-key-detail-refresh label span {{
      color: #6b7177 !important;
      opacity: 1 !important;
      visibility: visible !important;
  }}
  .st-key-detail-refresh [data-testid="stWidgetLabel"] p {{
      font-size: var(--ca-run-meta-size) !important;
      font-weight: 600 !important;
      white-space: nowrap;
      line-height: 1 !important;
      margin: 0 !important;
      display: flex !important;
      align-items: center !important;
  }}
  .st-key-detail-refresh [data-testid="stToggle"],
  .st-key-detail-refresh [data-testid="stCheckbox"],
  .st-key-detail-refresh [role="switch"],
  .st-key-detail-refresh [data-baseweb="switch"] {{
      opacity: 1 !important;
      visibility: visible !important;
      margin: 0 !important;
      min-height: 0 !important;
      align-self: center !important;
  }}
  .st-key-detail-refresh [data-baseweb="switch"] {{
      background-color: #c4c9ce !important;
      border: 1px solid #aeb4ba !important;
      min-width: 2rem !important;
      min-height: 1rem !important;
      padding: 0.12rem !important;
      box-sizing: border-box !important;
  }}
  .st-key-detail-refresh [data-baseweb="switch"][aria-checked="true"] {{
      background-color: {BRAND_ORANGE} !important;
      border-color: {BRAND_ORANGE} !important;
  }}
  .st-key-detail-refresh [data-baseweb="switch"] > div {{
      background-color: #ffffff !important;
      box-shadow: 0 1px 3px rgba(19, 21, 22, 0.18) !important;
  }}
  .ca-detail-head {{
      margin: 0;
      max-width: 100%;
  }}
  .ca-detail-meta-bar {{
      width: 100%;
      box-sizing: border-box;
      padding: 0;
      display: flex;
      align-items: center;
      min-height: 0;
  }}
  /* Meta line — single compact row, vertically centered. */
  .ca-detail-meta {{
      display: flex;
      flex-direction: row;
      flex-wrap: nowrap;
      align-items: center;
      gap: 0.22rem;
      font-size: var(--ca-run-meta-size);
      color: #7a8086;
      font-style: italic;
      width: 100%;
      line-height: 1;
      height: auto;
      min-height: var(--ca-detail-meta-height);
      min-width: 0;
  }}
  .ca-detail-meta > * {{
      display: inline-flex;
      align-items: center;
      align-self: center;
      flex: 0 0 auto;
      line-height: 1;
      margin: 0;
  }}
  .ca-detail-meta .ca-badge {{
      font-style: normal;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      align-self: center;
      height: 1rem;
      padding: 0 0.32rem;
      line-height: 1;
      margin: 0;
      vertical-align: middle;
  }}
  .ca-detail-meta .ca-run-metaline {{
      display: inline-flex;
      align-items: center;
      align-self: center;
      gap: 0.12rem;
      white-space: nowrap;
      line-height: 1;
  }}
  .ca-detail-meta .ca-run-metaline .mi {{
      font-style: normal;
      font-size: 0.88em;
      line-height: 1;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 1em;
      height: 1em;
      flex: 0 0 1em;
  }}
  .ca-detail-meta .ca-local-dt {{
      display: inline-flex;
      align-items: center;
      line-height: 1;
  }}
  .ca-detail-meta .ca-detail-sep {{
      line-height: 1;
      align-self: center;
  }}
  .ca-detail-meta .ca-trigger-user {{
      line-height: 1;
  }}
  .ca-detail-meta .ca-run-metaline,
  .ca-detail-meta .ca-badge,
  .ca-detail-meta .ca-loglink,
  .ca-detail-meta .ca-log-sep,
  .ca-detail-meta .ca-detail-sep {{
      flex: 0 0 auto;
      white-space: nowrap;
  }}
  .st-key-detail-download-log .ca-step-link-disabled {{
      display: inline-flex !important;
      align-items: center !important;
      min-height: var(--ca-detail-meta-height) !important;
      line-height: 1 !important;
      font-size: var(--ca-run-meta-size) !important;
  }}
  .ca-detail-sep {{
      color: #c2c7cc;
      font-style: normal;
  }}
  .ca-trigger-user {{
      font-style: normal;
      font-weight: 700;
      color: {BRAND_INK};
  }}
  .ca-detail-status {{
      margin-top: 0.55rem;
      display: flex;
      align-items: center;
      gap: 0.55rem;
  }}
  .ca-log-sep {{
      color: #c2c7cc;
  }}
  .ca-loglink {{
      color: {BRAND_ORANGE};
      font-size: 0.86rem;
      font-weight: 600;
      text-decoration: none;
  }}
  .ca-loglink:hover {{
      text-decoration: underline;
  }}
  /* Tighter vertical stack: title → meta → orange divider. */
  .st-key-ca-detail-header .ca-title-rule {{
      margin: 0 !important;
      display: block;
  }}
  .st-key-ca-detail-header > [data-testid="stVerticalBlock"],
  .st-key-ca-detail-header > [data-testid="stVerticalBlockBorderWrapper"] {{
      gap: 0 !important;
  }}
  .st-key-ca-detail-header > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"] {{
      margin: 0 !important;
      padding: 0 !important;
  }}
  .st-key-ca-detail-header .st-key-ca-detail-title-row {{
      margin-bottom: -0.1rem !important;
  }}
  .st-key-ca-detail-header > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:last-child {{
      margin-top: -0.2rem !important;
      line-height: 0 !important;
  }}
  .st-key-ca-detail-header > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:last-child [data-testid="stHtml"],
  .st-key-ca-detail-header > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:last-child iframe {{
      margin: 0 !important;
      padding: 0 !important;
      display: block !important;
      line-height: 0 !important;
  }}
  .st-key-ca-detail-meta-row [data-testid="stElementContainer"] {{
      margin-bottom: 0 !important;
      padding-bottom: 0 !important;
  }}

  /* Run details — step list spacing. */
  .st-key-ca-steps > [data-testid="stVerticalBlock"],
  .st-key-ca-steps > [data-testid="stVerticalBlockBorderWrapper"] > [data-testid="stVerticalBlock"],
  .st-key-ca-steps [data-testid="stFragment"] > [data-testid="stVerticalBlock"],
  .st-key-ca-steps [data-testid="stVerticalBlock"]:has(> [class*="st-key-stepcard_"]) {{
      gap: 4px !important;
      align-items: stretch !important;
      margin: 0 !important;
      padding: 0 !important;
  }}

  /* Stable shell while the steps fragment mounts or polls. */
  .st-key-ca-steps [data-testid="stFragment"] {{
      display: block;
      width: 100%;
  }}

  /* Each step is a bordered card — detail row + arrow in columns. */
  [class*="st-key-stepcard_"] {{
      position: relative;
      border: 1px solid #e3e6e8;
      border-radius: 10px;
      padding: 8px 16px;
      background: #ffffff;
      min-height: 0;
  }}

  [class*="st-key-stepcard_"] > [data-testid="stVerticalBlock"],
  [class*="st-key-stepcard_"] > [data-testid="stVerticalBlockBorderWrapper"] > [data-testid="stVerticalBlock"] {{
      gap: 0 !important;
      margin: 0 !important;
      padding: 0 !important;
      position: relative !important;
      min-height: 0 !important;
      height: auto !important;
  }}
  [class*="st-key-stepcard_"] [data-testid="stHorizontalBlock"] {{
      display: flex !important;
      flex-direction: row !important;
      flex-wrap: nowrap !important;
      align-items: center !important;
      width: 100% !important;
      margin: 0 !important;
      padding: 0 !important;
      gap: 0.25rem !important;
      min-height: 0 !important;
  }}
  [class*="st-key-stepcard_"] [data-testid="column"] {{
      display: flex !important;
      align-items: center !important;
      justify-content: flex-start !important;
      min-height: 0 !important;
      padding-top: 0 !important;
      padding-bottom: 0 !important;
      margin: 0 !important;
  }}
  [class*="st-key-stepcard_"] [data-testid="column"]:first-child {{
      flex: 1 1 auto !important;
      min-width: 0 !important;
      width: auto !important;
  }}
  [class*="st-key-stepcard_"] [data-testid="column"]:last-child {{
      flex: 0 0 auto !important;
      width: auto !important;
      min-width: 1.5rem !important;
      max-width: 1.75rem !important;
      justify-content: center !important;
  }}
  [class*="st-key-stepcard_"] [data-testid="column"]:first-child [data-testid="stVerticalBlock"],
  [class*="st-key-stepcard_"] [data-testid="column"]:first-child [data-testid="stElementContainer"] {{
      margin: 0 !important;
      padding: 0 !important;
      min-height: 0 !important;
      width: 100% !important;
      max-width: 100% !important;
      overflow: hidden !important;
  }}
  [class*="st-key-stepcard_"] [data-testid="column"]:last-child [data-testid="stVerticalBlock"],
  [class*="st-key-stepcard_"] [data-testid="column"]:last-child [data-testid="stElementContainer"] {{
      width: auto !important;
      justify-content: center !important;
      margin: 0 !important;
      padding: 0 !important;
  }}
  [class*="st-key-stepcard_"] [data-testid="column"]:first-child [data-testid="stHtml"] iframe {{
      display: block !important;
      width: 100% !important;
      margin: 0 !important;
      padding: 0 !important;
      border: none !important;
      background: transparent !important;
      min-height: 18px !important;
      max-height: 24px !important;
      height: auto !important;
      overflow: hidden !important;
  }}

  /* Header row: name + status icon on the left, "More actions" before the arrow column. */
  .ca-step-head {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      min-height: 18px;
  }}
  .ca-step-left {{
      display: flex;
      align-items: center;
      gap: 8px;
      min-width: 0;
  }}
  .ca-step-name {{
      font-size: 14px;
      font-weight: 600;
      color: {BRAND_INK};
      line-height: 1.25;
  }}
  .ca-step-status-img {{
      flex: 0 0 auto;
      width: 18px;
      height: 18px;
      object-fit: contain;
      display: block;
  }}
  .ca-step-more {{
      flex: 0 0 auto;
      font-size: 13px;
      font-weight: 600;
      color: #6b7177;
      white-space: nowrap;
      margin-left: 8px;
  }}
  .ca-step-detail-panel {{
      display: grid;
      grid-template-rows: 0fr;
      transition: grid-template-rows 0.32s cubic-bezier(0.4, 0, 0.2, 1);
  }}
  .ca-step-detail-panel--open {{
      grid-template-rows: 1fr;
  }}
  .ca-step-detail {{
      display: flex;
      flex-direction: column;
      gap: 0.2rem;
      overflow: hidden;
      min-height: 0;
      margin-top: 0;
      padding-top: 0;
      border-top: 1px solid transparent;
      opacity: 0;
      transform: translateY(-6px);
      transition:
          opacity 0.24s ease,
          transform 0.32s cubic-bezier(0.4, 0, 0.2, 1),
          margin-top 0.32s cubic-bezier(0.4, 0, 0.2, 1),
          padding-top 0.32s cubic-bezier(0.4, 0, 0.2, 1),
          border-color 0.24s ease;
  }}
  .ca-step-detail-panel--open .ca-step-detail {{
      margin-top: 0.5rem;
      padding-top: 0.5rem;
      border-top-color: #eef0f2;
      opacity: 1;
      transform: translateY(0);
  }}
  @media (prefers-reduced-motion: reduce) {{
      .ca-step-detail-panel,
      .ca-step-detail {{
          transition: none !important;
      }}
  }}
  .ca-step-time {{
      font-size: 0.78rem;
      color: #6b7177;
      white-space: nowrap;
  }}
  /* Step dropdown action links: Details · Download Step Log */
  [class*="st-key-step_links_"],
  [class*="st-key-step_links_"] > [data-testid="stVerticalBlock"],
  [class*="st-key-step_links_"] > [data-testid="stVerticalBlockBorderWrapper"] {{
      display: flex !important;
      flex-direction: row !important;
      align-items: center !important;
      flex-wrap: nowrap !important;
      gap: var(--ca-detail-inline-gap) !important;
      width: 100% !important;
      margin: 0.5rem 0 0 0 !important;
      padding: 0.5rem 0 0 0 !important;
      border-top: 1px solid #eef0f2;
  }}
  [class*="st-key-step_links_"] > [data-testid="stElementContainer"] {{
      width: auto !important;
      flex: 0 0 auto !important;
      margin: 0 !important;
      padding: 0 !important;
      position: static !important;
  }}
  .ca-step-links-inline {{
      display: inline-flex;
      align-items: center;
      gap: var(--ca-detail-inline-gap);
  }}
  .ca-step-link-disabled {{
      color: #b0b5ba;
      font-size: 0.86rem;
      font-weight: 600;
      cursor: not-allowed;
  }}
  [class*="st-key-step_details_"] .stButton,
  [class*="st-key-step_details_"] .stButton button {{
      width: auto !important;
      min-height: 0 !important;
      margin: 0 !important;
      padding: 0 !important;
      background: transparent !important;
      border: none !important;
      box-shadow: none !important;
      color: {BRAND_ORANGE} !important;
      font-size: 0.86rem !important;
      font-weight: 600 !important;
  }}
  [class*="st-key-step_details_"] .stButton button:hover {{
      text-decoration: underline;
      color: {BRAND_ORANGE} !important;
  }}
  [class*="st-key-step_links_"] .stDownloadButton,
  [class*="st-key-step_links_"] .stDownloadButton button {{
      width: auto !important;
      min-height: 0 !important;
      margin: 0 !important;
      padding: 0 !important;
      background: transparent !important;
      border: none !important;
      box-shadow: none !important;
      color: {BRAND_ORANGE} !important;
      font-size: 0.86rem !important;
      font-weight: 600 !important;
  }}
  [class*="st-key-step_links_"] .stDownloadButton button:hover {{
      text-decoration: underline;
      color: {BRAND_ORANGE} !important;
  }}

  /* Expand/collapse arrow — right column only (not Details / Download Step Log). */
  [class*="st-key-stepcard_"] [data-testid="column"]:last-child [data-testid="stElementContainer"]:has(.stButton) {{
      position: static !important;
      width: auto !important;
      height: auto !important;
      margin: 0 !important;
      padding: 0 !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
  }}
  [class*="st-key-stepcard_"] [data-testid="column"]:last-child .stButton {{
      width: auto !important;
      margin: 0 !important;
      min-height: 0 !important;
      display: flex !important;
      align-items: center !important;
  }}
  [class*="st-key-stepcard_"] [data-testid="column"]:last-child .stButton button {{
      width: auto !important;
      min-width: 1.25rem !important;
      min-height: 18px !important;
      height: 18px !important;
      background: transparent !important;
      border: none !important;
      box-shadow: none !important;
      color: #8a9097;
      padding: 0 !important;
      display: inline-flex !important;
      align-items: center !important;
      justify-content: center !important;
  }}
  [class*="st-key-stepcard_"] [data-testid="column"]:last-child .stButton button [data-testid="stMarkdownContainer"] {{
      display: none !important;
  }}
  [class*="st-key-stepcard_"] [data-testid="column"]:last-child .stButton button [data-testid="stIconMaterial"] {{
      font-size: 1.15rem !important;
      width: 1.15rem !important;
      height: 1.15rem !important;
      line-height: 1 !important;
      transition: transform 0.28s cubic-bezier(0.4, 0, 0.2, 1);
  }}
  [class*="st-key-stepcard_"]:has(.ca-step-head--open) [data-testid="column"]:last-child .stButton button [data-testid="stIconMaterial"] {{
      transform: rotate(90deg);
  }}
  [class*="st-key-stepcard_"] [data-testid="column"]:last-child .stButton button svg {{
      width: 1.15rem !important;
      height: 1.15rem !important;
  }}
  [class*="st-key-stepcard_"] [data-testid="column"]:last-child .stButton button:hover,
  [class*="st-key-stepcard_"] [data-testid="column"]:last-child .stButton button:hover [data-testid="stIconMaterial"],
  [class*="st-key-stepcard_"] [data-testid="column"]:last-child .stButton button:hover svg {{
      color: {BRAND_ORANGE} !important;
      fill: {BRAND_ORANGE} !important;
  }}

  /* ---------- Step detail dialog — translucent overlay + strict light panel ---------- */
  [data-testid="stBackdrop"] {{
      background-color: rgba(19, 21, 22, 0.38) !important;
      backdrop-filter: blur(4px) !important;
      -webkit-backdrop-filter: blur(4px) !important;
  }}
  [data-testid="stDialog"],
  div[data-baseweb="modal"],
  div[data-baseweb="modal"] > div,
  [data-testid="stDialog"] > div {{
      background: transparent !important;
      background-color: transparent !important;
      color-scheme: light only !important;
  }}
  [data-testid="stDialog"] [role="dialog"],
  [data-testid="stDialog"] [data-testid="stModal"],
  [data-testid="stDialog"] [data-testid="stModalContainer"],
  div[data-baseweb="modal"] [data-baseweb="modal-dialog"] {{
      background: rgba(255, 255, 255, 0.97) !important;
      backdrop-filter: blur(14px) saturate(1.1) !important;
      -webkit-backdrop-filter: blur(14px) saturate(1.1) !important;
      color: {BRAND_INK} !important;
      color-scheme: light only !important;
      border: 1px solid rgba(227, 230, 232, 0.95) !important;
      border-radius: 12px !important;
      box-shadow: 0 22px 64px rgba(19, 21, 22, 0.22) !important;
      --background-color: #ffffff !important;
      --secondary-background-color: #f6f7f8 !important;
      --text-color: {BRAND_INK} !important;
  }}
  [data-testid="stDialog"] header,
  [data-testid="stDialog"] [data-testid="stModalHeader"] {{
      background: transparent !important;
      border-bottom: 1px solid #eef0f2 !important;
  }}
  [data-testid="stDialog"] header h1,
  [data-testid="stDialog"] [data-testid="stModalHeader"] h1 {{
      display: none !important;
  }}
  [data-testid="stDialog"] [data-testid="stModalCloseButton"],
  [data-testid="stDialog"] button[aria-label="Close"] {{
      color: #6b7177 !important;
      background: transparent !important;
  }}
  .ca-step-dialog-title {{
      font-size: 1.35rem;
      font-weight: 700;
      color: {BRAND_INK};
      margin: 0 0 1rem 0;
      padding: 0;
  }}
  .ca-step-dialog-body {{
      color: {BRAND_INK};
      background: transparent;
  }}
  .ca-step-dialog-fields {{
      display: grid;
      grid-template-columns: max-content 1fr;
      gap: 0.45rem 1rem;
      margin: 0 0 1.25rem 0;
      font-size: 0.92rem;
  }}
  .ca-step-dialog-fields dt {{
      margin: 0;
      font-weight: 600;
      color: {BRAND_INK};
  }}
  .ca-step-dialog-fields dd {{
      margin: 0;
      color: #3d4348;
  }}
  .ca-step-dialog-section {{
      font-size: 1rem;
      font-weight: 700;
      color: {BRAND_INK};
      margin: 0 0 0.55rem 0;
  }}
  .ca-step-dialog-table-wrap {{
      overflow-x: auto;
      border: 1px solid #e3e6e8;
      border-radius: 8px;
      background: #ffffff;
  }}
  .ca-step-dialog-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.82rem;
      background: #ffffff;
      color: {BRAND_INK};
  }}
  .ca-step-dialog-table th,
  .ca-step-dialog-table td {{
      padding: 0.45rem 0.65rem;
      text-align: left;
      border-bottom: 1px solid #eef0f2;
      color: {BRAND_INK};
      background: #ffffff;
  }}
  .ca-step-dialog-table th {{
      background: #f6f7f8 !important;
      font-weight: 600;
      color: #3d4348;
  }}
  .ca-step-dialog-table tr:last-child td {{
      border-bottom: none;
  }}
  .ca-step-dialog-empty {{
      color: #6b7177;
      font-size: 0.88rem;
      margin: 0;
  }}
  .ca-step-dialog-error {{
      color: #cf222e;
      background: #ffebe9;
      border: 1px solid #ff8182;
      border-radius: 8px;
      padding: 0.65rem 0.85rem;
      font-size: 0.9rem;
  }}
</style>
"""


def apply_global_styles() -> None:
    """Inject the shared CSS into the current page.

    Uses ``st.markdown(..., unsafe_allow_html=True)`` rather than ``st.html``:
    in Streamlit 1.42+ a ``<style>`` block injected via ``st.html`` lands in the
    DOM but no longer takes effect, which silently drops all custom styling.
    """
    st.markdown(_GLOBAL_CSS, unsafe_allow_html=True)
    inject_local_datetime_js()


def render_logo(path: str | Path | None = None, width: int | None = None) -> None:
    """Render the SVG logo, top-flush and left-aligned like ``render_title``.

    Reads the SVG from the repo-root ``assets/`` folder (resolved absolutely so
    it works regardless of the current working directory) and embeds it as a
    data URI so it renders inline (typically inside the sidebar).
    """
    logo_path = Path(path or DEFAULT_LOGO_PATH)
    width_attr = ""
    if width is not None:
        width_attr = f' style="width:{int(width)}px;max-width:100%;height:auto;"'
    try:
        svg = logo_path.read_text(encoding="utf-8")
    except OSError:
        st.caption("Logo not found.")
        return
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    st.html(
        f"""
        <div class="ca-logo">
          <img src="data:image/svg+xml;base64,{b64}" alt="Clone automation logo"{width_attr} />
        </div>
        """
    )


STATUS_COLORS = {
    "COMPLETED": "green",
    "RUNNING": "blue",
    "PENDING": "gray",
    "FAILED": "red",
    "SKIPPED": "orange",
    "ABORTED": "violet",
}


def status_color(status: str) -> str:
    """Map a clone status to a badge color name."""
    return STATUS_COLORS.get((status or "").upper(), "gray")


def _esc(text) -> str:
    """Escape user- or DB-sourced text for safe HTML embedding."""
    if text is None or text == "":
        return html.escape("—", quote=True)
    return html.escape(str(text), quote=True)


def status_badge_html(status: str) -> str:
    """Return an HTML badge span for a status (colored)."""
    safe = _esc(status)
    return f'<span class="ca-badge {status_color(status)}">{safe}</span>'


def step_attempts_table_html(attempts: list[dict]) -> str:
    """Light-mode HTML table for step attempt history."""
    if not attempts:
        return '<p class="ca-step-dialog-empty">No attempts recorded for this function.</p>'

    rows = []
    for row in attempts:
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(row.get('attempt_number', '')))}</td>"
            f"<td>{html.escape(str(row.get('clone_function_run_id', '')))}</td>"
            f"<td>{html.escape(str(row.get('status', '')))}</td>"
            f"<td>{dt_html(row.get('start_time'))}</td>"
            f"<td>{dt_html(row.get('end_time'))}</td>"
            f"<td>{html.escape(fmt_duration(row.get('start_time'), row.get('end_time')))}</td>"
            "</tr>"
        )
    return (
        '<div class="ca-step-dialog-table-wrap">'
        '<table class="ca-step-dialog-table">'
        "<thead><tr>"
        "<th>Attempt</th>"
        "<th>Clone function run ID</th>"
        "<th>Status</th>"
        "<th>Start</th>"
        "<th>End</th>"
        "<th>Duration</th>"
        "</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table></div>"
    )


def step_detail_dialog_html(detail: dict, function_name: str) -> str:
    """Full light-mode dialog body (HTML only — avoids Streamlit dark widgets)."""
    safe_name = html.escape(function_name)
    status = status_badge_html(detail.get("status", ""))
    attempts_html = step_attempts_table_html(detail.get("attempts") or [])
    return (
        f'<div class="ca-step-dialog-body">'
        f'<div class="ca-step-dialog-title">Function step details · {safe_name}</div>'
        f'<dl class="ca-step-dialog-fields">'
        f"<dt>Clone run ID</dt><dd>{html.escape(str(detail.get('clone_run_id', '—')))}</dd>"
        f"<dt>Clone function run ID</dt>"
        f"<dd>{html.escape(str(detail.get('clone_function_run_id', '—')))}</dd>"
        f"<dt>Status</dt><dd>{status}</dd>"
        f"<dt>Start</dt><dd>{dt_html(detail.get('start_time'))}</dd>"
        f"<dt>End</dt><dd>{dt_html(detail.get('end_time'))}</dd>"
        f"<dt>Duration</dt>"
        f"<dd>{html.escape(fmt_duration(detail.get('start_time'), detail.get('end_time')))}</dd>"
        f"</dl>"
        f'<div class="ca-step-dialog-section">Attempts</div>'
        f"{attempts_html}"
        f"</div>"
    )


def step_detail_dialog_error_html(message: str) -> str:
    safe = html.escape(message)
    return f'<div class="ca-step-dialog-body"><p class="ca-step-dialog-error">{safe}</p></div>'


# Status -> PNG asset in the repo-root ``assets/`` folder. Used on the run
# details step rows in place of the text badge.
STATUS_ASSETS = {
    "COMPLETED": "completed.png",
    "RUNNING": "running.png",
    "PENDING": "pending.png",
    "FAILED": "failed.png",
    "SKIPPED": "skipped.png",
    "ABORTED": "aborted.png",
}


def status_image_html(status: str, size: int = STATUS_ICON_PX) -> str:
    """Return a square ``<img>`` of the status icon (falls back to text badge).

    The icons are square, so a fixed ``size`` keeps every icon — and the
    function name beside it — aligned in a clean vertical column across rows.
    """
    filename = STATUS_ASSETS.get((status or "").upper())
    if not filename:
        return status_badge_html(status)
    try:
        uri = _asset_data_uri(filename)
    except OSError:
        # Asset missing/unreadable on this host — degrade to the text badge
        # rather than crashing the whole page.
        return status_badge_html(status)
    label = _esc((status or "unknown").title())
    return (
        f'<img class="ca-step-status-img" src="{uri}" '
        f'alt="{label}" title="{label}" '
        f'style="width:{size}px;height:{size}px;" />'
    )


def step_detail_panel_html(
    run_id: int,
    index: int,
    is_open: bool,
    start_time,
    end_time,
) -> str:
    """Collapsible step detail panel with smooth open/close animation."""
    panel_class = "ca-step-detail-panel--open" if is_open else "ca-step-detail-panel--closed"
    panel_id = f"step-panel-{run_id}-{index}"
    store_key = f"ca-step-{run_id}-{index}"
    start = dt_html(start_time)
    end = dt_html(end_time)
    return f"""
<div id="{panel_id}" class="ca-step-detail-panel {panel_class}">
  <div class="ca-step-detail">
    <div class="ca-step-time">Start: {start}</div>
    <div class="ca-step-time">End: {end}</div>
  </div>
</div>
<script>
(function () {{
  var panel = document.getElementById("{panel_id}");
  if (!panel) return;
  var key = "{store_key}";
  var wasOpen = sessionStorage.getItem(key) === "1";
  var isOpen = panel.classList.contains("ca-step-detail-panel--open");
  if (!wasOpen && isOpen) {{
    panel.classList.remove("ca-step-detail-panel--open");
    void panel.offsetHeight;
    panel.classList.add("ca-step-detail-panel--open");
  }} else if (wasOpen && !isOpen) {{
    panel.classList.add("ca-step-detail-panel--open");
    void panel.offsetHeight;
    panel.classList.remove("ca-step-detail-panel--open");
  }}
  sessionStorage.setItem(key, isOpen ? "1" : "0");
  if (window.caFormatLocalDatetimes) window.caFormatLocalDatetimes(panel);
}})();
</script>
"""


def fmt_dt(value) -> str:
    """Format an ISO datetime string (or None) for display."""
    return fmt_dt_fallback(value)


def fmt_dt_compact(value) -> str:
    """Format an ISO datetime string (or None) as ``ddmmyy hhmmss``."""
    if not value:
        return "—"
    try:
        dt = datetime.fromisoformat(str(value))
        if dt.tzinfo is not None:
            dt = dt.astimezone()
        return dt.strftime("%d%m%y %H%M%S")
    except (ValueError, TypeError):
        return str(value)


def fmt_relative_update(value) -> str:
    """Human-friendly update time (server-local fallback for plain text)."""
    return fmt_relative_update_fallback(value)


def fmt_started(value) -> str:
    """Format a start timestamp (server-local fallback for plain text)."""
    return fmt_started_fallback(value)


def fmt_duration(start, end) -> str:
    """Elapsed time between two timestamps, e.g. "1h 9m" / "9m 30s" / "45s"."""
    if not start or not end:
        return "—"
    try:
        s = datetime.fromisoformat(str(start))
        e = datetime.fromisoformat(str(end))
    except (ValueError, TypeError):
        return "—"
    secs = int((e - s).total_seconds())
    if secs < 0:
        return "—"
    hours, rem = divmod(secs, 3600)
    mins, sec = divmod(rem, 60)
    if hours:
        return f"{hours}h {mins}m"
    if mins:
        return f"{mins}m {sec}s" if sec else f"{mins}m"
    return f"{sec}s"


def render_run_card(run: dict) -> bool:
    """Render a run card as one line plus a redirect button on the right.

    client · Run # · source→target · user · status · started · updated · duration.
    Meta segment (times) is smaller and italic. Returns ``True`` when the redirect
    button is clicked.
    """
    rid = run.get("clone_run_id")
    client = (
        run.get("client_name")
        or run.get("clientName")
        or run.get("client")
        or "—"
    )
    failed_step = run.get("failed_function_name")
    failed_step_html = ""
    if failed_step:
        failed_step_html = (
            f'<span class="sep">&middot;</span>'
            f'<span class="ca-run-metaline">Failed step: {_esc(failed_step)}</span>'
        )
    info_html = (
        f'<div class="ca-run"><div class="ca-run-oneline" '
        f'style="display:flex;align-items:center;width:100%;min-height:1.65rem;line-height:1.25;">'
        f'<span class="ca-run-primary">'
        f'<span class="ca-run-client">{_esc(client)}</span>'
        f'<span class="sep">&middot;</span>'
        f'<span>Run #{_esc(rid)}</span>'
        f'<span class="sep">&middot;</span>'
        f'<span>{_esc(run.get("source_name", "—"))}'
        f'<span class="arrow">&#8594;</span>{_esc(run.get("target_name", "—"))}</span>'
        f'<span class="sep">&middot;</span>'
        f'<span>{_esc(run.get("user_name", "—"))}</span>'
        f'<span class="sep">&middot;</span>'
        f'{status_badge_html(run.get("status", ""))}'
        f'</span>'
        f'<div class="ca-run-meta-part" '
        f'style="margin-left:auto;display:flex;align-items:center;gap:12px;'
        f'min-width:420px;justify-content:flex-end;box-sizing:border-box;">'
        f'<span class="ca-run-metaline">'
        f'<span class="mi mi-start">&#9654;</span> Started {started_html(run.get("start_date"))}'
        f'</span>'
        f'<span class="sep">&middot;</span>'
        f'<span class="ca-run-metaline">'
        f'<span class="mi mi-upd">&#8635;</span> {relative_update_html(run.get("last_update"))}'
        f'</span>'
        f'<span class="sep">&middot;</span>'
        f'<span class="ca-run-metaline">'
        f'<span class="mi mi-dur">&#9201;</span> '
        f'{fmt_duration(run.get("start_date"), run.get("last_update"))}'
        f'</span>'
        f'{failed_step_html}'
        f'</div></div></div>'
    )
    with st.container(key=f"runcard_{rid}"):
        detail_col, arrow_col = st.columns(
            [1, 0.06],
            gap="small",
            vertical_alignment="center",
        )
        with detail_col:
            st.html(info_html)
        with arrow_col:
            clicked = st.button(
                "",
                key=f"open_run_{rid}",
                icon=":material/arrow_right:",
                help="View run details",
                type="tertiary",
            )
    return clicked


def render_status(is_live: bool, last_refresh: datetime | None = None) -> None:
    """Render the bottom-of-sidebar backend status card.

    A glowing green dot (live) or red dot (offline) sits to the left of a
    "Last refresh on ..." line formatted in the browser's local timezone.
    Call inside a ``with st.sidebar:`` block, after nav.
    """
    last_refresh = last_refresh or datetime.now(timezone.utc)
    state = "is-live" if is_live else "is-offline"
    with st.container(key="ca-status"):
        emit_html(
            f"""
            <div class="ca-status {state}">
              <span class="ca-dot-wrap"><span class="ca-dot"></span></span>
              {refresh_html(last_refresh)}
            </div>
            """
        )


DEFAULT_PAGE = "Home"

# Single source of truth for navigation: drives both the real ``st.Page``
# registry (build_pages) and the custom sidebar (render_sidebar_nav).
NAV: list[dict] = [
    {"kind": "item", "title": "Home", "icon": "space_dashboard",
     "key": "nav_home", "module": "app_pages/home.py"},
    {"kind": "group", "title": "Admin", "badge": "Coming soon!", "items": [
        {"title": "Clients", "icon": "work", "key": "nav_clients",
         "module": "app_pages/clients.py", "disabled": True},
        {"title": "Team", "icon": "group", "key": "nav_team",
         "module": "app_pages/team.py", "disabled": True},
        {"title": "Targets", "icon": "dns", "key": "nav_targets",
         "module": "app_pages/targets.py", "disabled": True},
    ]},
    {"kind": "group", "title": "Clone Setup", "items": [
        {"title": "DB Config", "icon": "database", "key": "nav_db", "module": "app_pages/db_config.py"},
        {"title": "EBS Config", "icon": "deployed_code", "key": "nav_ebs", "module": "app_pages/ebs_config.py"},
        {"title": "Integrations", "icon": "hub", "key": "nav_integrations", "module": "app_pages/integrations.py"},
    ]},
    {"kind": "divider"},
    {"kind": "item", "title": "Execute Clone", "icon": "play_arrow",
     "key": "nav_execute", "module": "app_pages/execute_clone.py"},
    {"kind": "item", "title": "Run History", "icon": "history",
     "key": "nav_history", "module": "app_pages/run_history.py"},
]


def _iter_nav_items(nav: list[dict] = NAV):
    """Yield every clickable nav item (flattening groups)."""
    for entry in nav:
        if entry["kind"] == "item":
            yield entry
        elif entry["kind"] == "group":
            yield from entry["items"]


# Pages that must be registered with st.navigation (so st.switch_page can reach
# them) but should NOT appear in the custom sidebar.
HIDDEN_PAGES = [
    {"title": "Run details", "icon": "history", "module": "app_pages/run_details.py"},
]


def build_pages() -> dict:
    """Build the ``st.Page`` registry keyed by page title.

    Pass ``list(build_pages().values())`` to ``st.navigation``. Includes the
    sidebar pages plus hidden detail pages reachable via ``st.switch_page``.
    """
    pages = {}
    for item in _iter_nav_items():
        pages[item["title"]] = st.Page(
            item["module"],
            title=item["title"],
            icon=f":material/{item['icon']}:",
            default=(item["title"] == DEFAULT_PAGE),
        )
    for item in HIDDEN_PAGES:
        pages[item["title"]] = st.Page(
            item["module"],
            title=item["title"],
            icon=f":material/{item['icon']}:",
        )
    return pages


def goto_page(title: str) -> None:
    """Switch to a registered page by its title.

    Reuses the exact ``st.Page`` instances registered with ``st.navigation``
    (stored in session state by ``app.py``); a freshly built ``st.Page`` may not
    match the registry, which is why string-path navigation was unreliable.
    """
    pages = st.session_state.get("_pages") or build_pages()
    st.switch_page(pages[title])


def clear_run_details_state() -> None:
    """Remove run-details keys from session state and URL query params."""
    rid = st.session_state.get("selected_run_id")
    if rid is not None:
        st.session_state.pop(f"auto_refresh_{rid}", None)
    st.session_state.pop("selected_run_id", None)
    st.session_state.pop("selected_run", None)
    st.session_state.pop("_auto_refresh_run", None)
    if "run" in st.query_params:
        del st.query_params["run"]


def consume_pending_navigation() -> None:
    """Honour a pending page switch requested by a widget on the prior rerun."""
    target = st.session_state.pop("_ca_navigate", None)
    if not target:
        return
    clear_run_details_state()
    goto_page(target)


def request_page(title: str) -> None:
    """Queue navigation to ``title``; call ``consume_pending_navigation()`` early on rerun."""
    st.session_state["_ca_navigate"] = title
    st.rerun()


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
                st.html('<hr class="ca-nav-divider-line" />')


def render_title(title: str, subtitle: str | None = None) -> None:
    """Render a top-flush page title with an accent rule.

    Call ``apply_global_styles()`` before this so the CSS is available.
    """
    subtitle_html = f'<p class="ca-subtitle">{subtitle}</p>' if subtitle else ""
    st.html(
        f"""
        <div class="ca-page-header">
          <div class="ca-title">
            <h1>{title}</h1>
          </div>
          {subtitle_html}
          <hr class="ca-title-rule" />
        </div>
        """
    )

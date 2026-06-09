"""Reusable custom CSS for the Clone Automation dashboard.

Import and call ``apply_global_styles()`` once near the top of any page
(after ``st.set_page_config``) to get consistent styling across the app.
"""

import base64
import html
from datetime import datetime
from functools import lru_cache
from pathlib import Path

import streamlit as st

BRAND_ORANGE = "#e87511"
BRAND_INK = "#131516"
STATUS_ICON_PX = 18
ACTION_ICON_REM = "1.1rem"

# Repo root is the parent of the ``frontend/`` package that holds this file.
REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LOGO_PATH = REPO_ROOT / "assets" / "logo.svg"


@lru_cache(maxsize=None)
def _asset_data_uri(filename: str) -> str:
    """Read a file from ``assets/`` and return it as a base64 data URI."""
    data = (REPO_ROOT / "assets" / filename).read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    suffix = Path(filename).suffix.lower()
    mime = "image/svg+xml" if suffix == ".svg" else "image/png"
    return f"data:{mime};base64,{b64}"


_ABORT_BTN_ICON = _asset_data_uri("aborted.png")
_SKIP_BTN_ICON = _asset_data_uri("skipped.png")

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
      margin: 0.4rem 0 0.55rem 0;
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
  .st-key-ca-nav > [data-testid="stVerticalBlock"] {{
      gap: 0 !important;
      align-items: stretch;
  }}

  .st-key-ca-nav [data-testid="stElementContainer"] {{
      align-items: flex-start;
      text-align: left;
      margin: 0 !important;
      padding: 0 !important;
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
      padding: 0.35rem 0.55rem;
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
      padding: 0.35rem 0.55rem;
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

  /* Indent the items nested inside a group, with tight vertical padding.
     Remove the separator border between the header and the content. */
  .st-key-ca-nav [data-testid="stExpanderDetails"] {{
      padding-left: 0.6rem;
      padding-top: 0.1rem;
      padding-bottom: 0;
      border: none !important;
      box-shadow: none !important;
  }}

  /* Remove the expander's own trailing space before the divider. */
  .st-key-ca-nav [data-testid="stExpander"] {{
      margin-bottom: 0 !important;
  }}

  /* Thin divider line before Execute Clone (no st.divider wrapper gap). */
  .ca-nav-divider-line {{
      display: block;
      height: 1px;
      border: none;
      margin: 0.12rem 0.55rem 0.12rem 0.55rem;
      background: rgba(232, 117, 17, 0.25);
  }}

  /* ---------- Run History filters + Execute Clone form ---------- */
  .st-key-ca-run-filters,
  .st-key-ca-execute-clone-form {{
      margin-top: -0.35rem !important;
      margin-bottom: 0.5rem;
  }}
  .st-key-ca-run-filters [data-testid="stVerticalBlock"],
  .st-key-ca-execute-clone-form [data-testid="stVerticalBlock"] {{
      gap: 0.25rem !important;
  }}
  .st-key-ca-run-filters [data-testid="stHorizontalBlock"],
  .st-key-ca-execute-clone-form [data-testid="stHorizontalBlock"] {{
      align-items: flex-end;
      gap: 0.65rem;
  }}
  .st-key-ca-run-filters [data-testid="stWidgetLabel"] p,
  .st-key-ca-execute-clone-form [data-testid="stWidgetLabel"] p {{
      color: #6b7177 !important;
      font-size: 0.82rem;
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
  .st-key-ca-execute-clone-actions {{
      margin-top: 0.35rem;
  }}
  .st-key-ca-execute-clone-actions .stButton button {{
      font-weight: 700 !important;
  }}

  /* ---------- Sidebar bottom status card ---------- */

  /* Make the sidebar a full-height column so the status can sit at the bottom. */
  [data-testid="stSidebarUserContent"] {{
      display: flex;
      flex-direction: column;
      min-height: calc(100vh - 5.5rem);
  }}

  [data-testid="stSidebarUserContent"] > [data-testid="stVerticalBlock"] {{
      flex: 1 1 auto;
  }}

  /* Push the status block to the very bottom. */
  [data-testid="stSidebarUserContent"] :has(> .st-key-ca-status) {{
      margin-top: auto;
  }}

  /* Single inline row: glowing dot + last-refresh text. No card. */
  .ca-status {{
      display: flex;
      align-items: center;
      gap: 0.55rem;
      padding: 0.2rem 0.15rem;
  }}

  .ca-status .ca-dot {{
      width: 10px;
      height: 10px;
      border-radius: 50%;
      flex: 0 0 auto;
  }}

  .ca-status .ca-refresh-text {{
      font-size: 0.75rem;
      color: #6b7177;
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
      70%  {{ box-shadow: 0 0 0 9px rgba(34, 197, 94, 0); }}
      100% {{ box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }}
  }}

  /* ---------- Status badges (reused on cards + steps) ---------- */
  .ca-badge {{
      display: inline-block;
      padding: 0.12rem 0.6rem;
      border-radius: 999px;
      font-size: 0.72rem;
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
  .st-key-ca-runs > [data-testid="stVerticalBlock"] {{
      gap: 0.7rem;
  }}

  /* Card container: two-line info on the left, redirect button at far right. */
  [class*="st-key-runcard_"] {{
      position: relative;
      border: 1px solid #e3e6e8;
      border-radius: 12px;
      padding: 0.75rem 3rem 0.75rem 1.1rem;
      background: #ffffff;
      transition: border-color 0.15s ease, box-shadow 0.15s ease;
  }}
  [class*="st-key-runcard_"]:hover {{
      border-color: {BRAND_ORANGE};
      box-shadow: 0 2px 12px rgba(19, 21, 22, 0.07);
  }}

  /* Pull the button's whole element container out of flow and pin it to the
     card's right edge (Streamlit sets each element container position:relative,
     so positioning the .stButton wrapper alone anchors it to the wrong box). */
  [class*="st-key-runcard_"] [data-testid="stElementContainer"]:has(.stButton) {{
      position: absolute !important;
      right: 0.5rem;
      top: 50%;
      transform: translateY(-50%);
      width: auto !important;
      margin: 0 !important;
      z-index: 3;
  }}
  [class*="st-key-runcard_"] .stButton {{
      width: auto !important;
      margin: 0 !important;
  }}
  /* Borderless icon button, pinned to the extreme right, vertically centered. */
  [class*="st-key-runcard_"] .stButton button {{
      width: auto !important;
      min-height: 0 !important;
      background: transparent !important;
      border: none !important;
      box-shadow: none !important;
      color: #8a9097;
      padding: 0.3rem;
  }}
  /* Make the redirect arrow noticeably larger, sized relative to the text. */
  [class*="st-key-runcard_"] .stButton button [data-testid="stIconMaterial"] {{
      font-size: 1.9rem !important;
      width: 1.9rem !important;
      height: 1.9rem !important;
  }}
  [class*="st-key-runcard_"] .stButton button svg {{
      width: 1.9rem !important;
      height: 1.9rem !important;
  }}
  [class*="st-key-runcard_"] .stButton button:hover {{
      background: transparent !important;
      color: {BRAND_ORANGE};
  }}
  [class*="st-key-runcard_"] .stButton button:hover svg,
  [class*="st-key-runcard_"] .stButton button:hover [data-testid="stIconMaterial"] {{
      color: {BRAND_ORANGE};
  }}

  .ca-run-line1 {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 0.45rem;
      font-size: 0.92rem;
      font-weight: 600;
      color: {BRAND_INK};
  }}
  .ca-run-line1 .sep {{
      color: #c2c7cc;
      font-weight: 400;
  }}
  .ca-run-line1 .ca-run-client {{
      font-weight: 700;
  }}
  .ca-run-line1 .arrow {{
      color: {BRAND_ORANGE};
      margin: 0 0.3rem;
  }}
  .ca-run-meta {{
      margin-top: 0.45rem;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 0.45rem;
      font-size: 0.78rem;
      color: #6b7177;
      font-style: italic;
  }}
  .ca-run-meta .sepm {{
      color: #c2c7cc;
      font-style: normal;
  }}
  .ca-run-metaline {{
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
  }}
  .ca-run-metaline .mi {{
      font-size: 0.92rem;
      line-height: 1;
  }}
  .ca-run-metaline .mi-start {{ color: #1a7f37; }}
  .ca-run-metaline .mi-upd   {{ color: {BRAND_ORANGE}; }}
  .ca-run-metaline .mi-dur   {{ color: #8a9097; }}

  /* ---------- Run details header ---------- */
  .ca-run-sep {{ color: #c2c7cc; font-weight: 400; }}
  /* Title parts use the same gap as the middot-separated heading text. */
  .ca-detail-title-parts {{
      display: inline-flex;
      align-items: center;
      gap: var(--ca-detail-inline-gap);
      margin: 0;
      padding: 0;
      font-size: 2.6rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      color: {BRAND_INK};
      line-height: 1.1;
      white-space: nowrap;
  }}
  .ca-detail-title-parts .ca-run-sep {{
      flex: 0 0 auto;
  }}
  .ca-detail-title-parts .arrow {{
      color: {BRAND_ORANGE};
  }}
  /* Dot between Abort and Skip — same style as the title separators. */
  .ca-action-sep {{
      display: inline-flex;
      align-items: center;
      font-size: 1.35rem;
      font-weight: 400;
      color: #c2c7cc;
      line-height: 1;
  }}
  /* Title row: heading then Abort · Skip with identical gap. */
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
  }}
  .st-key-ca-detail-title-row [data-testid="stElementContainer"] {{
      width: auto !important;
      flex: 0 0 auto !important;
      margin: 0 !important;
      padding: 0 !important;
      max-width: none !important;
  }}
  .st-key-detail-actions,
  .st-key-detail-actions [data-testid="stVerticalBlock"],
  .st-key-detail-actions [data-testid="stVerticalBlockBorderWrapper"] {{
      display: flex !important;
      flex-direction: row !important;
      align-items: center !important;
      flex-wrap: nowrap !important;
      gap: var(--ca-detail-inline-gap) !important;
      width: auto !important;
  }}
  .st-key-detail-actions [data-testid="stElementContainer"] {{
      width: auto !important;
      flex: 0 0 auto !important;
      margin: 0 !important;
      padding: 0 !important;
  }}
  .ca-detail-title {{
      margin: 0;
  }}
  /* Abort / Skip — icon + label, tight beside the heading. */
  .st-key-detail_abort .stButton,
  .st-key-detail_skip .stButton {{
      width: auto !important;
      margin: 0 !important;
  }}
  .st-key-detail_abort .stButton button,
  .st-key-detail_skip .stButton button {{
      display: inline-flex !important;
      align-items: center !important;
      justify-content: center !important;
      gap: 0.55rem !important;
      width: auto !important;
      font-size: 1.35rem !important;
      font-weight: 700 !important;
      padding: 0.35rem 0.9rem !important;
      min-height: 0 !important;
      border-radius: 8px !important;
      white-space: nowrap !important;
  }}
  .st-key-detail_abort .stButton button p,
  .st-key-detail_skip .stButton button p {{
      margin: 0 !important;
      padding: 0 !important;
      line-height: 1 !important;
  }}
  .st-key-detail_abort .stButton button::before,
  .st-key-detail_skip .stButton button::before {{
      content: "";
      display: inline-block;
      width: {ACTION_ICON_REM};
      height: {ACTION_ICON_REM};
      flex: 0 0 auto;
      background-position: center;
      background-repeat: no-repeat;
      background-size: contain;
  }}
  .st-key-detail_abort .stButton button::before {{
      background-image: url({_ABORT_BTN_ICON});
  }}
  .st-key-detail_skip .stButton button::before {{
      background-image: url({_SKIP_BTN_ICON});
  }}
  .st-key-detail_abort .stButton button {{
      background: #ffebe9 !important;
      color: #cf222e !important;
      border: 1px solid #ff8182 !important;
  }}
  .st-key-detail_skip .stButton button {{
      background: #fff1e5 !important;
      color: #bc4c00 !important;
      border: 1px solid #fd8c73 !important;
  }}
  .st-key-detail_abort .stButton button:disabled,
  .st-key-detail_skip .stButton button:disabled {{
      opacity: 0.45 !important;
      cursor: not-allowed !important;
  }}
  /* Meta row: full-width facts + Download Log; Auto refresh pinned far right. */
  .st-key-ca-detail-meta-row {{
      position: relative;
      width: 100%;
      margin: 0 !important;
      padding: 0 !important;
  }}
  .st-key-ca-detail-meta-row > [data-testid="stVerticalBlock"],
  .st-key-ca-detail-meta-row > [data-testid="stVerticalBlockBorderWrapper"] {{
      display: flex !important;
      flex-direction: row !important;
      align-items: center !important;
      flex-wrap: nowrap !important;
      width: 100% !important;
      margin: 0 !important;
      padding: 0 !important;
      gap: 0 !important;
  }}
  .st-key-ca-detail-meta-row > [data-testid="stElementContainer"] {{
      margin: 0 !important;
      padding: 0 !important;
  }}
  .st-key-ca-detail-meta-row > [data-testid="stElementContainer"]:first-child {{
      flex: 1 1 auto !important;
      width: 100% !important;
      min-width: 0 !important;
  }}
  .ca-detail-meta-bar {{
      width: 100%;
      box-sizing: border-box;
      padding-right: 10rem;
  }}
  .st-key-ca-detail-meta-row .st-key-detail-refresh {{
      position: absolute !important;
      right: 0 !important;
      top: 50% !important;
      transform: translateY(-50%) !important;
      width: auto !important;
      margin: 0 !important;
      z-index: 2;
      display: flex !important;
      align-items: center;
      justify-content: flex-end;
      background: #ffffff !important;
      padding-left: 0.75rem !important;
      opacity: 1 !important;
      visibility: visible !important;
      flex: 0 0 auto !important;
  }}
  .st-key-ca-detail-meta-row .st-key-detail-refresh [data-testid="stVerticalBlock"],
  .st-key-ca-detail-meta-row .st-key-detail-refresh [data-testid="stElementContainer"] {{
      display: flex !important;
      align-items: center;
      justify-content: flex-end;
      width: auto !important;
      margin: 0 !important;
      opacity: 1 !important;
      visibility: visible !important;
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
      font-size: 0.82rem !important;
      font-weight: 600 !important;
      white-space: nowrap;
  }}
  .st-key-detail-refresh [data-testid="stToggle"],
  .st-key-detail-refresh [data-testid="stCheckbox"],
  .st-key-detail-refresh [role="switch"],
  .st-key-detail-refresh [data-baseweb="switch"] {{
      opacity: 1 !important;
      visibility: visible !important;
  }}
  .st-key-detail-refresh [data-baseweb="switch"] {{
      background-color: #c4c9ce !important;
      border: 1px solid #aeb4ba !important;
      min-width: 2.35rem !important;
      min-height: 1.35rem !important;
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
  /* Meta line: Triggered by · Started · Updated · Duration · status · Download Log */
  .ca-detail-meta {{
      display: flex;
      flex-direction: row;
      flex-wrap: wrap;
      align-items: center;
      gap: var(--ca-detail-inline-gap);
      row-gap: 0.2rem;
      font-size: 0.86rem;
      color: #6b7177;
      font-style: italic;
      width: 100%;
  }}
  .ca-detail-meta .ca-run-metaline,
  .ca-detail-meta .ca-badge,
  .ca-detail-meta .ca-loglink,
  .ca-detail-meta .ca-log-sep,
  .ca-detail-meta .ca-detail-sep {{
      flex: 0 0 auto;
      white-space: nowrap;
  }}
  .ca-detail-meta .ca-run-metaline {{
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
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
  /* Tighter gap between meta row and orange accent bar on run details. */
  .st-key-ca-detail-header .ca-title-rule {{
      margin: 0 0 0.35rem 0;
  }}
  .st-key-ca-detail-header > [data-testid="stVerticalBlock"] {{
      gap: 0.08rem !important;
  }}
  .st-key-ca-detail-meta-row [data-testid="stElementContainer"] {{
      margin-bottom: 0 !important;
      padding-bottom: 0 !important;
  }}

  /* Borderless "Back to Run History" link-style button. */
  .st-key-back_to_runs .stButton button {{
      background: transparent !important;
      border: none !important;
      box-shadow: none !important;
      outline: none !important;
      padding: 0.3rem 0.2rem !important;
      color: {BRAND_ORANGE} !important;
      font-weight: 600;
      cursor: pointer !important;
      opacity: 1 !important;
  }}
  .st-key-back_to_runs .stButton button p,
  .st-key-back_to_runs .stButton button svg,
  .st-key-back_to_runs .stButton button [data-testid="stIconMaterial"] {{
      color: {BRAND_ORANGE} !important;
      fill: {BRAND_ORANGE} !important;
  }}
  .st-key-back_to_runs .stButton button:hover,
  .st-key-back_to_runs .stButton button:focus,
  .st-key-back_to_runs .stButton button:active {{
      background: transparent !important;
      border: none !important;
      box-shadow: none !important;
      outline: none !important;
      color: {BRAND_ORANGE} !important;
  }}
  .st-key-back_to_runs .stButton button:hover p {{
      text-decoration: underline;
  }}
  .st-key-back_to_runs .stButton button:hover svg,
  .st-key-back_to_runs .stButton button:hover p,
  .st-key-back_to_runs .stButton button:hover [data-testid="stIconMaterial"] {{
      color: {BRAND_ORANGE} !important;
  }}

  /* ---------- Step rows (run details) ---------- */
  .st-key-ca-steps > [data-testid="stVerticalBlock"] {{
      gap: 0.4rem;
  }}

  /* Each step is a bordered card. Right padding reserves room for the toggle
     arrow, which is pinned to the card's right edge (like Run History cards). */
  [class*="st-key-stepcard_"] {{
      position: relative;
      border: 1px solid #e3e6e8;
      border-radius: 10px;
      padding: 0.5rem 2.8rem 0.5rem 1.1rem;
      background: #ffffff;
  }}

  /* Header row: name + status icon on the left, "More actions" on the right. */
  .ca-step-head {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.7rem;
      min-height: 1.9rem;
  }}
  /* Icon first, name right beside it — both aligned in vertical columns.
     Tight gap so the name sits close to its status icon. */
  .ca-step-left {{
      display: flex;
      align-items: center;
      gap: 0.45rem;
  }}
  .ca-step-name {{
      font-weight: 600;
      color: {BRAND_INK};
  }}
  .ca-step-status-img {{
      flex: 0 0 auto;
      object-fit: contain;
      display: block;
  }}
  .ca-step-more {{
      font-size: 0.85rem;
      font-weight: 600;
      color: #6b7177;
      white-space: nowrap;
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

  /* Expand/collapse arrow only — not Details or other step actions. */
  [class*="st-key-stepcard_"] [class*="st-key-more_"],
  [class*="st-key-stepcard_"] [class*="st-key-more_"] > [data-testid="stElementContainer"] {{
      position: absolute !important;
      right: 0.5rem;
      top: 0.5rem;
      height: 1.9rem;
      display: flex;
      align-items: center;
      width: auto !important;
      margin: 0 !important;
      z-index: 3;
  }}
  [class*="st-key-stepcard_"] [class*="st-key-more_"] .stButton {{
      width: auto !important;
      margin: 0 !important;
  }}
  [class*="st-key-stepcard_"] [class*="st-key-more_"] .stButton button {{
      width: auto !important;
      min-height: 0 !important;
      background: transparent !important;
      border: none !important;
      box-shadow: none !important;
      color: #8a9097;
      padding: 0.1rem;
  }}
  [class*="st-key-stepcard_"] [class*="st-key-more_"] .stButton button [data-testid="stIconMaterial"] {{
      font-size: 1.9rem !important;
      width: 1.9rem !important;
      height: 1.9rem !important;
      line-height: 1 !important;
      transition: transform 0.28s cubic-bezier(0.4, 0, 0.2, 1);
  }}
  [class*="st-key-stepcard_"]:has(.ca-step-head--open) [class*="st-key-more_"] .stButton button [data-testid="stIconMaterial"] {{
      transform: rotate(90deg);
  }}
  [class*="st-key-stepcard_"] [class*="st-key-more_"] .stButton button svg {{
      width: 1.9rem !important;
      height: 1.9rem !important;
  }}
  [class*="st-key-stepcard_"] [class*="st-key-more_"] .stButton button:hover,
  [class*="st-key-stepcard_"] [class*="st-key-more_"] .stButton button:hover [data-testid="stIconMaterial"],
  [class*="st-key-stepcard_"] [class*="st-key-more_"] .stButton button:hover svg {{
      color: {BRAND_ORANGE} !important;
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


def status_badge_html(status: str) -> str:
    """Return an HTML badge span for a status (colored)."""
    return f'<span class="ca-badge {status_color(status)}">{status or "—"}</span>'


def step_attempts_table_html(attempts: list[dict]) -> str:
    """Light-mode HTML table for step attempt history."""
    if not attempts:
        return '<p class="ca-step-dialog-empty">No attempts recorded for this function.</p>'

    rows = []
    for row in attempts:
        current = "Yes" if row.get("is_current") else ""
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(row.get('attempt_number', '')))}</td>"
            f"<td>{html.escape(str(row.get('clone_function_run_id', '')))}</td>"
            f"<td>{html.escape(str(row.get('status', '')))}</td>"
            f"<td>{html.escape(fmt_dt(row.get('start_time')))}</td>"
            f"<td>{html.escape(fmt_dt(row.get('end_time')))}</td>"
            f"<td>{html.escape(current)}</td>"
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
        "<th>Current</th>"
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
        f"<dt>Start</dt><dd>{html.escape(fmt_dt(detail.get('start_time')))}</dd>"
        f"<dt>End</dt><dd>{html.escape(fmt_dt(detail.get('end_time')))}</dd>"
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
    label = (status or "").title()
    return (
        f'<img class="ca-step-status-img" src="{uri}" '
        f'alt="{label}" title="{label}" '
        f'style="width:{size}px;height:{size}px;" />'
    )


def step_action_link_html(step_log_href: str | None) -> str:
    """Download Step Log link with middot spacing matching the title row."""
    if step_log_href:
        link = (
            f'<a class="ca-loglink" href="{step_log_href}" download>'
            f"Download Step Log</a>"
        )
    else:
        link = '<span class="ca-step-link-disabled">Download Step Log</span>'
    return (
        f'<span class="ca-step-links-inline">'
        f'<span class="ca-detail-sep">&middot;</span>{link}'
        f"</span>"
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
    start = fmt_dt(start_time)
    end = fmt_dt(end_time)
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
}})();
</script>
"""


def fmt_dt(value) -> str:
    """Format an ISO datetime string (or None) for display."""
    if not value:
        return "—"
    try:
        return datetime.fromisoformat(str(value)).strftime("%b %d, %Y %I:%M %p")
    except (ValueError, TypeError):
        return str(value)


def fmt_dt_compact(value) -> str:
    """Format an ISO datetime string (or None) as ``ddmmyy hhmmss``."""
    if not value:
        return "—"
    try:
        return datetime.fromisoformat(str(value)).strftime("%d%m%y %H%M%S")
    except (ValueError, TypeError):
        return str(value)


def fmt_relative_update(value) -> str:
    """Human-friendly update time, e.g. "Updated today at 2:18 PM",
    "Updated yesterday at 9:05 AM", or "Updated on Jun 08 at 1:09 PM"."""
    if not value:
        return "Not updated yet"
    try:
        dt = datetime.fromisoformat(str(value))
    except (ValueError, TypeError):
        return f"Updated {value}"
    time_str = dt.strftime("%I:%M %p").lstrip("0")
    days = (datetime.now().date() - dt.date()).days
    if days == 0:
        return f"Updated today at {time_str}"
    if days == 1:
        return f"Updated yesterday at {time_str}"
    return f"Updated on {dt.strftime('%b %d')} at {time_str}"


def fmt_started(value) -> str:
    """Format a start timestamp as "08 Jun 2026, 1:08 PM" (local time)."""
    if not value:
        return "Not started"
    try:
        dt = datetime.fromisoformat(str(value))
    except (ValueError, TypeError):
        return str(value)
    return dt.strftime("%d %b %Y, ") + dt.strftime("%I:%M %p").lstrip("0")


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
    """Render a run card with two info lines and a redirect button on the right.

    Line 1: client · Run # · source -> target · user · status (colored).
    Line 2: started · last update (ddmmyy hhmmss). Returns ``True`` when the
    redirect button is clicked.
    """
    rid = run.get("clone_run_id")
    client = (
        run.get("client_name")
        or run.get("clientName")
        or run.get("client")
        or "—"
    )
    info_html = f"""
        <div class="ca-run">
          <div class="ca-run-line1">
            <span class="ca-run-client">{client}</span>
            <span class="sep">&middot;</span>
            <span>Run #{rid}</span>
            <span class="sep">&middot;</span>
            <span>{run.get('source_name', '—')}<span class="arrow">&#8594;</span>{run.get('target_name', '—')}</span>
            <span class="sep">&middot;</span>
            <span>{run.get('user_name', '—')}</span>
            <span class="sep">&middot;</span>
            {status_badge_html(run.get('status', ''))}
          </div>
          <div class="ca-run-meta">
            <span class="ca-run-metaline">
              <span class="mi mi-start">&#9654;</span> Started {fmt_started(run.get('start_date'))}
            </span>
            <span class="sepm">&middot;</span>
            <span class="ca-run-metaline">
              <span class="mi mi-upd">&#8635;</span> {fmt_relative_update(run.get('last_update'))}
            </span>
            <span class="sepm">&middot;</span>
            <span class="ca-run-metaline">
              <span class="mi mi-dur">&#9201;</span> {fmt_duration(run.get('start_date'), run.get('last_update'))}
            </span>
          </div>
        </div>
    """
    with st.container(key=f"runcard_{rid}"):
        st.html(info_html)
        return st.button(
            "",
            key=f"open_run_{rid}",
            icon=":material/arrow_right:",
            help="View run details",
        )


def render_status(is_live: bool, last_refresh: datetime | None = None) -> None:
    """Render the bottom-of-sidebar backend status card.

    A glowing green dot (live) or red dot (offline) sits to the left of a
    "Last refresh on ..." line. Call inside a ``with st.sidebar:`` block,
    after the navigation.
    """
    last_refresh = last_refresh or datetime.now()
    state = "is-live" if is_live else "is-offline"
    stamp = last_refresh.strftime("%b %d, %Y at %I:%M %p")
    with st.container(key="ca-status"):
        st.html(
            f"""
            <div class="ca-status {state}">
              <span class="ca-dot"></span>
              <span class="ca-refresh-text">Last refresh on {stamp}</span>
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
        <div class="ca-title">
          <h1>{title}</h1>
        </div>
        {subtitle_html}
        <hr class="ca-title-rule" />
        """
    )

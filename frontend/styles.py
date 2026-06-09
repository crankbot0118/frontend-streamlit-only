"""Reusable custom CSS for the Clone Automation dashboard.

Import and call ``apply_global_styles()`` once near the top of any page
(after ``st.set_page_config``) to get consistent styling across the app.
"""

import base64
from datetime import datetime
from functools import lru_cache
from pathlib import Path

import streamlit as st

BRAND_ORANGE = "#e87511"
BRAND_INK = "#131516"

# Repo root is the parent of the ``frontend/`` package that holds this file.
REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LOGO_PATH = REPO_ROOT / "assets" / "logo.svg"

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

  /* ---------- Run History filters ---------- */
  .st-key-ca-run-filters {{
      margin-top: -0.35rem !important;
      margin-bottom: 0.5rem;
  }}
  .st-key-ca-run-filters [data-testid="stVerticalBlock"] {{
      gap: 0.25rem !important;
  }}
  .st-key-ca-run-filters [data-testid="stHorizontalBlock"] {{
      align-items: flex-end;
      gap: 0.65rem;
  }}
  .st-key-ca-run-filters [data-testid="stWidgetLabel"] p {{
      color: #6b7177 !important;
      font-size: 0.82rem;
      font-weight: 600;
  }}
  /* Force white filter controls (select + date) on light background. */
  .st-key-ca-run-filters [data-testid="stSelectbox"] > div > div,
  .st-key-ca-run-filters [data-testid="stSelectbox"] [data-baseweb="select"] > div,
  .st-key-ca-run-filters [data-testid="stDateInput"] > div > div,
  .st-key-ca-run-filters [data-testid="stDateInput"] [data-baseweb="input"],
  .st-key-ca-run-filters [data-testid="stDateInput"] input {{
      background-color: #ffffff !important;
      color: {BRAND_INK} !important;
      border-color: #e3e6e8 !important;
  }}
  .st-key-ca-run-filters [data-testid="stSelectbox"] svg,
  .st-key-ca-run-filters [data-testid="stDateInput"] svg {{
      color: #6b7177 !important;
      fill: #6b7177 !important;
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
  .st-key-ca-detail-header [data-testid="stHorizontalBlock"] {{
      align-items: center;
  }}
  .ca-detail-title {{
      margin: 0;
  }}
  /* Abort / Skip — sized to sit beside the page heading. */
  .st-key-detail_abort .stButton,
  .st-key-detail_skip .stButton {{
      width: 100% !important;
  }}
  .st-key-detail_abort .stButton button,
  .st-key-detail_skip .stButton button {{
      width: 100% !important;
      font-size: 1.35rem !important;
      font-weight: 700 !important;
      padding: 0.3rem 0.75rem !important;
      min-height: 0 !important;
      border-radius: 8px !important;
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
  /* Auto refresh toggle pinned to the far right of the meta row. */
  .st-key-detail-refresh {{
      display: flex;
      justify-content: flex-end;
      align-items: center;
      width: 100%;
  }}
  .st-key-detail-refresh [data-testid="stWidgetLabel"] p {{
      font-size: 0.82rem !important;
      font-weight: 600 !important;
      color: #6b7177 !important;
      white-space: nowrap;
  }}
  .ca-detail-head {{
      margin: 0.15rem 0 0.2rem 0;
  }}
  /* Single-line meta: Triggered by <user> · Started · Updated · Duration · status · View Log */
  .ca-detail-meta {{
      display: flex;
      flex-direction: row;
      flex-wrap: wrap;
      align-items: center;
      gap: 0.45rem;
      font-size: 0.86rem;
      color: #6b7177;
      font-style: italic;
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
  .ca-step-detail {{
      display: flex;
      flex-direction: column;
      gap: 0.2rem;
      margin-top: 0.5rem;
      padding-top: 0.5rem;
      border-top: 1px solid #eef0f2;
      animation: ca-step-expand 0.18s ease-out;
  }}

  /* Minimal fade + slide-in when the "More actions" dropdown opens. */
  @keyframes ca-step-expand {{
      from {{ opacity: 0; transform: translateY(-4px); }}
      to   {{ opacity: 1; transform: translateY(0); }}
  }}
  .ca-step-time {{
      font-size: 0.78rem;
      color: #6b7177;
      white-space: nowrap;
  }}

  /* Toggle arrow button pinned to the card's right edge, aligned with the
     header row — the same redirect arrow style used on the Run History cards. */
  [class*="st-key-stepcard_"] [data-testid="stElementContainer"]:has(.stButton) {{
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
  [class*="st-key-stepcard_"] .stButton {{
      width: auto !important;
      margin: 0 !important;
  }}
  [class*="st-key-stepcard_"] .stButton button {{
      width: auto !important;
      min-height: 0 !important;
      background: transparent !important;
      border: none !important;
      box-shadow: none !important;
      color: #8a9097;
      padding: 0.1rem;
  }}
  [class*="st-key-stepcard_"] .stButton button [data-testid="stIconMaterial"] {{
      font-size: 1.9rem !important;
      width: 1.9rem !important;
      height: 1.9rem !important;
      line-height: 1 !important;
  }}
  [class*="st-key-stepcard_"] .stButton button svg {{
      width: 1.9rem !important;
      height: 1.9rem !important;
  }}
  [class*="st-key-stepcard_"] .stButton button:hover,
  [class*="st-key-stepcard_"] .stButton button:hover [data-testid="stIconMaterial"],
  [class*="st-key-stepcard_"] .stButton button:hover svg {{
      color: {BRAND_ORANGE} !important;
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


@lru_cache(maxsize=None)
def _asset_data_uri(filename: str) -> str:
    """Read a PNG from ``assets/`` and return it as a base64 data URI."""
    data = (REPO_ROOT / "assets" / filename).read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:image/png;base64,{b64}"


def status_image_html(status: str, size: int = 22) -> str:
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

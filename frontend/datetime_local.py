"""Browser-local datetime formatting for HTML rendered in Streamlit."""

from __future__ import annotations

import html
from datetime import datetime, timezone

import streamlit as st

_LOCAL_DT_JS = """
<script>
(function () {
  if (window.__caLocalDtInit) return;
  window.__caLocalDtInit = true;

  function pad2(n) {
    return n < 10 ? "0" + n : String(n);
  }

  function formatTime(dt) {
    return dt.toLocaleString(undefined, {
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
  }

  function formatDt(iso) {
    var dt = new Date(iso);
    if (Number.isNaN(dt.getTime())) return null;
    var month = dt.toLocaleString(undefined, { month: "short" });
    return month + " " + dt.getDate() + ", " + dt.getFullYear() + " " + formatTime(dt);
  }

  function formatStarted(iso) {
    var dt = new Date(iso);
    if (Number.isNaN(dt.getTime())) return null;
    var month = dt.toLocaleString(undefined, { month: "short" });
    return pad2(dt.getDate()) + " " + month + " " + dt.getFullYear() + ", " + formatTime(dt);
  }

  function formatRelativeUpdate(iso) {
    var dt = new Date(iso);
    if (Number.isNaN(dt.getTime())) return null;
    var now = new Date();
    var dtDay = new Date(dt.getFullYear(), dt.getMonth(), dt.getDate());
    var nowDay = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    var diffDays = Math.round((nowDay - dtDay) / 86400000);
    var time = formatTime(dt);
    if (diffDays === 0) return "Updated today at " + time;
    if (diffDays === 1) return "Updated yesterday at " + time;
    var month = dt.toLocaleString(undefined, { month: "short" });
    return "Updated on " + month + " " + pad2(dt.getDate()) + " at " + time;
  }

  function formatRefresh(iso) {
    var dt = new Date(iso);
    if (Number.isNaN(dt.getTime())) return null;
    var month = dt.toLocaleString(undefined, { month: "short" });
    return (
      "Last refresh on " +
      month +
      " " +
      dt.getDate() +
      ", " +
      dt.getFullYear() +
      " at " +
      formatTime(dt)
    );
  }

  var formatters = {
    dt: formatDt,
    started: formatStarted,
    relative_update: formatRelativeUpdate,
    refresh: formatRefresh,
  };

  window.caFormatLocalDatetimes = function (root) {
    var scope = root && root.querySelectorAll ? root : document;
    scope.querySelectorAll("[data-ca-dt-iso]:not([data-ca-dt-ready])").forEach(function (el) {
      var iso = el.getAttribute("data-ca-dt-iso");
      var fmt = el.getAttribute("data-ca-dt-fmt") || "dt";
      var prefix = el.getAttribute("data-ca-dt-prefix") || "";
      var fn = formatters[fmt];
      if (!fn || !iso) return;
      var text = fn(iso);
      if (text) {
        el.textContent = prefix + text;
        el.setAttribute("data-ca-dt-ready", "1");
      }
    });
  };

  caFormatLocalDatetimes(document);

  var observer = new MutationObserver(function (mutations) {
    mutations.forEach(function (m) {
      m.addedNodes.forEach(function (node) {
        if (node.nodeType === 1) caFormatLocalDatetimes(node);
      });
    });
  });
  if (document.body) {
    observer.observe(document.body, { childList: true, subtree: true });
  }
})();
</script>
"""


def parse_client_datetime(value) -> datetime | None:
    """Parse API/DB datetimes and normalize to UTC."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        try:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def iso_for_client(value) -> str | None:
    dt = parse_client_datetime(value)
    return dt.isoformat() if dt else None


def fmt_dt_fallback(value) -> str:
    dt = parse_client_datetime(value)
    if not dt:
        return "—"
    local = dt.astimezone()
    return local.strftime("%b %d, %Y %I:%M %p")


def fmt_started_fallback(value) -> str:
    dt = parse_client_datetime(value)
    if not dt:
        return "Not started"
    local = dt.astimezone()
    return local.strftime("%d %b %Y, ") + local.strftime("%I:%M %p").lstrip("0")


def fmt_relative_update_fallback(value) -> str:
    if not value:
        return "Not updated yet"
    dt = parse_client_datetime(value)
    if not dt:
        return f"Updated {value}"
    local = dt.astimezone()
    now = datetime.now(local.tzinfo)
    time_str = local.strftime("%I:%M %p").lstrip("0")
    days = (now.date() - local.date()).days
    if days == 0:
        return f"Updated today at {time_str}"
    if days == 1:
        return f"Updated yesterday at {time_str}"
    return f"Updated on {local.strftime('%b %d')} at {time_str}"


def fmt_refresh_fallback(value: datetime) -> str:
    dt = parse_client_datetime(value) or datetime.now(timezone.utc)
    local = dt.astimezone()
    return f"Last refresh on {local.strftime('%b %d, %Y at %I:%M %p')}"


def local_dt_span(
    value,
    fmt: str,
    *,
    prefix: str = "",
    empty: str = "—",
    css_class: str = "ca-local-dt",
) -> str:
    """Return a ``<span>`` that the browser formats in the user's local timezone."""
    iso = iso_for_client(value)
    if not iso:
        return html.escape(empty if not prefix else f"{prefix}{empty}")
    fallback = {
        "dt": fmt_dt_fallback,
        "started": fmt_started_fallback,
        "relative_update": fmt_relative_update_fallback,
        "refresh": fmt_refresh_fallback,
    }.get(fmt, fmt_dt_fallback)(value)
    label = html.escape(prefix + fallback if prefix else fallback)
    return (
        f'<span class="{css_class}" data-ca-dt-iso="{html.escape(iso, quote=True)}" '
        f'data-ca-dt-fmt="{html.escape(fmt, quote=True)}" '
        f'data-ca-dt-prefix="{html.escape(prefix, quote=True)}">{label}</span>'
    )


def dt_html(value) -> str:
    return local_dt_span(value, "dt")


def started_html(value) -> str:
    return local_dt_span(value, "started", empty="Not started")


def relative_update_html(value) -> str:
    return local_dt_span(value, "relative_update", empty="Not updated yet")


def refresh_html(value: datetime) -> str:
    return local_dt_span(
        value,
        "refresh",
        empty="Last refresh on —",
        css_class="ca-refresh-text",
    )


def inject_local_datetime_js() -> None:
    """Install the shared formatter script once per Streamlit session."""
    if st.session_state.get("_ca_local_dt_js"):
        return
    st.session_state["_ca_local_dt_js"] = True
    try:
        st.html(_LOCAL_DT_JS, unsafe_allow_javascript=True)
    except TypeError:
        st.html(_LOCAL_DT_JS)


def emit_html(body: str) -> None:
    """Render HTML and allow embedded scripts when supported."""
    body = (
        f"{body}\n"
        "<script>if(window.caFormatLocalDatetimes){window.caFormatLocalDatetimes(document);}</script>"
    )
    try:
        st.html(body, unsafe_allow_javascript=True)
    except TypeError:
        st.html(body)

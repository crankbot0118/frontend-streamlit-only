"""Home dashboard charts — clone activity bar chart and outcome donut."""

from __future__ import annotations

import html

import plotly.graph_objects as go

from kpi_helpers import CloneActivityStats, OutcomeBreakdown, format_duration
from styles import BRAND_INK, BRAND_ORANGE, BRAND_RED, UI_SCALE

CHART_SUCCESS = BRAND_ORANGE
CHART_FAILED = BRAND_RED
CHART_CANCELLED = "#9aa0a6"
CHART_GRID = "#eef0f2"
CHART_MUTED = "#6b7177"
CHART_AXIS = "#9aa0a6"

_PLOTLY_CONFIG = {"displayModeBar": False, "responsive": True}
ACTIVITY_CHART_HEIGHT = round(178 * UI_SCALE)
OUTCOME_CHART_HEIGHT = round(178 * UI_SCALE)
_CHART_FONT = round(12 * UI_SCALE)
_CHART_FONT_SM = round(11 * UI_SCALE)
_CHART_FONT_XS = round(10 * UI_SCALE)


def _base_layout(**overrides) -> dict:
    layout = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family="system-ui, -apple-system, Segoe UI, sans-serif",
            color=BRAND_INK,
            size=_CHART_FONT,
        ),
        margin=dict(l=0, r=0, t=round(4 * UI_SCALE), b=0),
        showlegend=False,
        hoverlabel=dict(
            bgcolor="#ffffff",
            bordercolor="#e3e6e8",
            font=dict(color=BRAND_INK, size=_CHART_FONT),
        ),
    )
    layout.update(overrides)
    return layout


def clone_activity_figure(stats: CloneActivityStats) -> go.Figure:
    labels = [bucket.label for bucket in stats.weeks]
    success = [bucket.successful for bucket in stats.weeks]
    failed = [bucket.failed for bucket in stats.weeks]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            name="Successful",
            x=labels,
            y=success,
            marker=dict(color=CHART_SUCCESS, line=dict(width=0), cornerradius=round(4 * UI_SCALE)),
            hovertemplate="%{x}<br>Successful: %{y}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            name="Failed",
            x=labels,
            y=failed,
            marker=dict(color=CHART_FAILED, line=dict(width=0), cornerradius=round(4 * UI_SCALE)),
            hovertemplate="%{x}<br>Failed: %{y}<extra></extra>",
        )
    )
    fig.update_layout(
        **_base_layout(
            barmode="stack",
            height=ACTIVITY_CHART_HEIGHT,
            bargap=0.38,
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.18,
                xanchor="left",
                x=0,
                font=dict(size=_CHART_FONT_SM, color=CHART_MUTED),
                traceorder="normal",
                itemsizing="constant",
                itemwidth=round(30 * UI_SCALE),
                entrywidth=round(90 * UI_SCALE),
                bgcolor="rgba(0,0,0,0)",
            ),
            showlegend=True,
            margin=dict(l=0, r=0, t=round(2 * UI_SCALE), b=round(38 * UI_SCALE)),
            xaxis=dict(
                showgrid=False,
                showline=False,
                zeroline=False,
                tickfont=dict(size=_CHART_FONT_SM, color=CHART_AXIS),
                tickmode="linear",
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor=CHART_GRID,
                gridwidth=1,
                zeroline=False,
                showline=False,
                tickfont=dict(size=_CHART_FONT_XS, color=CHART_AXIS),
                ticks="outside",
                ticklen=0,
                tickcolor="rgba(0,0,0,0)",
                automargin=True,
            ),
        )
    )
    return fig


def outcome_donut_figure(breakdown: OutcomeBreakdown) -> go.Figure:
    values = [slice_.count for slice_ in breakdown.slices]
    colors = [CHART_SUCCESS, CHART_FAILED, CHART_CANCELLED]
    center = (
        f"{breakdown.success_rate:.1f}%"
        if breakdown.success_rate is not None
        else "—"
    )
    total = sum(values)
    if total == 0:
        values = [1]
        colors = ["#eef0f2"]

    pull_vals = [0.018, 0.022, 0.018] if total else [0]
    fig = go.Figure(
        go.Pie(
            values=values,
            labels=[slice_.label for slice_ in breakdown.slices],
            hole=0.78,
            marker=dict(colors=colors, line=dict(color="#ffffff", width=round(5 * UI_SCALE))),
            sort=False,
            direction="clockwise",
            rotation=210,
            textinfo="none",
            hovertemplate="%{label}: %{value}<extra></extra>",
            pull=pull_vals,
        )
    )
    fig.update_layout(
        **_base_layout(
            height=OUTCOME_CHART_HEIGHT,
            margin=dict(l=0, r=0, t=round(4 * UI_SCALE), b=round(4 * UI_SCALE)),
        )
    )
    fig.add_annotation(
        text=f"<b>{center}</b>",
        x=0.5,
        y=0.56,
        showarrow=False,
        align="center",
        xref="paper",
        yref="paper",
        font=dict(
            size=round(27 * UI_SCALE),
            color=BRAND_INK,
            family="system-ui, -apple-system, Segoe UI, sans-serif",
        ),
    )
    fig.add_annotation(
        text="success rate",
        x=0.5,
        y=0.41,
        showarrow=False,
        align="center",
        xref="paper",
        yref="paper",
        font=dict(size=_CHART_FONT_SM, color=CHART_MUTED, family="system-ui, sans-serif"),
    )
    return fig


def clone_activity_header_html(stats: CloneActivityStats) -> str:
    avg = format_duration(stats.avg_duration_seconds)
    throughput = f"{stats.throughput_per_day:g}/day"
    return (
        '<div class="ca-clone-activity-top">'
        '<div class="ca-home-chart-head">'
        '<div class="ca-home-chart-title">Clone activity</div>'
        '<div class="ca-home-chart-sub">'
        "<em>Completed jobs per week · last 12 weeks</em></div>"
        "</div>"
        '<div class="ca-home-chart-metrics">'
        f'<div class="ca-home-chart-metric">'
        f'<strong>{stats.total_runs}</strong><span>Total runs</span></div>'
        f'<div class="ca-home-chart-metric">'
        f"<strong>{html.escape(avg)}</strong><span>Avg duration</span></div>"
        f'<div class="ca-home-chart-metric">'
        f"<strong>{html.escape(throughput)}</strong><span>Peak throughput</span></div>"
        "</div>"
        "</div>"
    )


def outcome_header_html(breakdown: OutcomeBreakdown) -> str:
    return (
        '<div class="ca-home-chart-head">'
        '<div class="ca-home-chart-title">Outcome breakdown</div>'
        f'<div class="ca-home-chart-sub"><em>Last {breakdown.days} days</em></div>'
        "</div>"
    )


def outcome_legend_html(breakdown: OutcomeBreakdown) -> str:
    rows = []
    for slice_ in breakdown.slices:
        rows.append(
            '<div class="ca-outcome-row">'
            f'<span class="ca-outcome-label">'
            f'<span class="ca-outcome-swatch {slice_.tone}"></span>'
            f"{html.escape(slice_.label)}</span>"
            f'<span class="ca-outcome-count">{slice_.count}</span>'
            f'<span class="ca-outcome-pct"><strong>{slice_.pct:.1f}%</strong></span>'
            "</div>"
        )
    return f'<div class="ca-outcome-legend">{"".join(rows)}</div>'


def plotly_config() -> dict:
    return dict(_PLOTLY_CONFIG)

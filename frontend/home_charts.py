"""Home dashboard charts — clone activity bar chart and outcome donut."""

from __future__ import annotations

import html

import plotly.graph_objects as go

from kpi_helpers import CloneActivityStats, OutcomeBreakdown, format_duration
from styles import BRAND_INK, BRAND_ORANGE, BRAND_RED

CHART_SUCCESS = BRAND_ORANGE
CHART_FAILED = BRAND_RED
CHART_CANCELLED = "#9aa0a6"
CHART_GRID = "#eef0f2"
CHART_MUTED = "#6b7177"

_PLOTLY_CONFIG = {"displayModeBar": False, "responsive": True}
ACTIVITY_CHART_HEIGHT = 178
OUTCOME_CHART_HEIGHT = 178


def _base_layout(**overrides) -> dict:
    layout = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family="system-ui, -apple-system, Segoe UI, sans-serif",
            color=BRAND_INK,
            size=12,
        ),
        margin=dict(l=0, r=0, t=4, b=0),
        showlegend=False,
        hoverlabel=dict(
            bgcolor="#ffffff",
            bordercolor="#e3e6e8",
            font=dict(color=BRAND_INK, size=12),
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
            marker=dict(color=CHART_SUCCESS, line=dict(width=0)),
            hovertemplate="%{x}<br>Successful: %{y}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            name="Failed",
            x=labels,
            y=failed,
            marker=dict(color=CHART_FAILED, line=dict(width=0), cornerradius=5),
            hovertemplate="%{x}<br>Failed: %{y}<extra></extra>",
        )
    )
    fig.update_layout(
        **_base_layout(
            barmode="stack",
            height=ACTIVITY_CHART_HEIGHT,
            bargap=0.36,
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.22,
                xanchor="left",
                x=0,
                font=dict(size=11, color=CHART_MUTED),
                traceorder="normal",
                itemsizing="constant",
                itemwidth=30,
                entrywidth=88,
                bgcolor="rgba(0,0,0,0)",
            ),
            showlegend=True,
            margin=dict(l=0, r=0, t=2, b=42),
            xaxis=dict(
                showgrid=False,
                showline=False,
                zeroline=False,
                tickfont=dict(size=12, color=CHART_MUTED),
                tickmode="linear",
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor=CHART_GRID,
                gridwidth=1,
                zeroline=False,
                showline=False,
                tickfont=dict(size=11, color=CHART_MUTED),
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

    fig = go.Figure(
        go.Pie(
            values=values,
            labels=[slice_.label for slice_ in breakdown.slices],
            hole=0.76,
            marker=dict(colors=colors, line=dict(color="#ffffff", width=3)),
            sort=False,
            direction="clockwise",
            rotation=210,
            textinfo="none",
            hovertemplate="%{label}: %{value}<extra></extra>",
            pull=[0, 0.03, 0] if total else [0],
        )
    )
    fig.update_layout(
        **_base_layout(
            height=OUTCOME_CHART_HEIGHT,
            margin=dict(l=0, r=0, t=0, b=0),
        )
    )
    fig.add_annotation(
        text=center,
        x=0.5,
        y=0.55,
        showarrow=False,
        align="center",
        xref="paper",
        yref="paper",
        font=dict(
            size=24,
            color=BRAND_INK,
            family="system-ui, -apple-system, Segoe UI, sans-serif",
        ),
    )
    fig.add_annotation(
        text="success rate",
        x=0.5,
        y=0.42,
        showarrow=False,
        align="center",
        xref="paper",
        yref="paper",
        font=dict(size=11, color=CHART_MUTED, family="system-ui, sans-serif"),
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

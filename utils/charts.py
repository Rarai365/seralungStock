"""
utils/charts.py
===============
Plotly chart builders for the Seralung Finance app.

All functions return a Plotly Figure object — they do NOT call
st.plotly_chart().  The caller decides how to render the figure.
This separation makes charts reusable and testable.

Mobile safety rules applied throughout:
  - Fixed heights with generous margins to prevent overflow clipping
  - Font sizes reduced on narrow viewports
  - Legend placed above the chart, never overlapping data
  - Hover templates are touch-friendly (no tiny labels)
  - No autosize=True (causes layout thrash on mobile Safari)
  - uniformtext prevents label collisions on small pie slices
"""

from __future__ import annotations

from typing import Dict, List, Optional
import plotly.graph_objects as go

from utils.styles import (
    BG_CARD, BG_BORDER,
    TEXT_PRIMARY, TEXT_MUTED,
    COLOR_PRIMARY, COLOR_PRIMARY_BG,
    COLOR_GREEN, COLOR_GREEN_BG,
    COLOR_AMBER, COLOR_AMBER_BG,
    COLOR_RED, COLOR_RED_BG,
    COLOR_TEAL, COLOR_TEAL_BG,
    COLOR_PURPLE, COLOR_PURPLE_BG,
    COLOR_LGREEN, COLOR_LGREEN_BG,
    COLOR_SLATE,
    FONT_SANS, FONT_MONO,
)


# ─────────────────────────────────────────────────────────────────────────────
# SHARED LAYOUT DEFAULTS
# ─────────────────────────────────────────────────────────────────────────────

_TRANSPARENT = "rgba(0,0,0,0)"

def _base_layout(**overrides) -> dict:
    """
    Return a base Plotly layout dict with app-consistent styling.
    Pass keyword arguments to override any default value.
    """
    layout = dict(
        paper_bgcolor=_TRANSPARENT,
        plot_bgcolor=_TRANSPARENT,
        font=dict(family=FONT_SANS, color=TEXT_PRIMARY),
        margin=dict(t=20, b=20, l=16, r=16),
        hoverlabel=dict(
            bgcolor=BG_CARD,
            bordercolor=BG_BORDER,
            font=dict(family=FONT_SANS, size=12, color=TEXT_PRIMARY),
        ),
    )
    layout.update(overrides)
    return layout


# ─────────────────────────────────────────────────────────────────────────────
# CIRCULAR GAUGE  (Financial Health / Readiness score)
# ─────────────────────────────────────────────────────────────────────────────

def build_circular_gauge(score: int, accent_colour: str) -> go.Figure:
    """
    Build a gauge chart for a 0–100 score (health or readiness).

    Design choices:
      - Fixed height 230px — safe on phones without overflow
      - Colour-coded background steps align with health_rating thresholds
      - Threshold line marks current score position clearly
    """
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number=dict(
            font=dict(size=44, family=FONT_SANS, color=accent_colour),
        ),
        gauge=dict(
            axis=dict(
                range=[0, 100],
                tickwidth=1,
                tickcolor=TEXT_MUTED,
                tickfont=dict(size=9, family=FONT_MONO, color=TEXT_MUTED),
            ),
            bar=dict(color=accent_colour, thickness=0.28),
            bgcolor=_TRANSPARENT,
            borderwidth=0,
            steps=[
                dict(range=[0,  25], color=COLOR_RED_BG),
                dict(range=[25, 45], color=COLOR_AMBER_BG),
                dict(range=[45, 65], color="#FFF7E0"),
                dict(range=[65, 80], color=COLOR_LGREEN_BG),
                dict(range=[80,100], color=COLOR_GREEN_BG),
            ],
            threshold=dict(
                line=dict(color=accent_colour, width=4),
                thickness=0.8,
                value=score,
            ),
        ),
    ))

    fig.update_layout(**_base_layout(
        height=230,
        margin=dict(t=18, b=8, l=22, r=22),
    ))
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# DONUT CHART  (expense breakdown, portfolio allocation)
# ─────────────────────────────────────────────────────────────────────────────

def build_donut_chart(
    labels: List[str],
    values: List[float],
    colors: List[str],
    center_label: str = "",
) -> go.Figure:
    """
    Build a donut / ring chart.

    Mobile safety:
      - uniformtext minsize=8 with mode="hide" prevents label collisions
      - textinfo limited to "percent" on very small slices
      - Fixed height 260px — won't overflow on small screens
      - Hover shows full label + percent without colour reliance
    """
    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.62,
        marker=dict(
            colors=colors,
            line=dict(color="#fff", width=2),
        ),
        # Show label + percent; very small slices hide cleanly via uniformtext
        textinfo="label+percent",
        textfont=dict(family=FONT_SANS, size=10, color=TEXT_PRIMARY),
        hovertemplate="<b>%{label}</b><br>%{percent}<extra></extra>",
        # Separate slices slightly so mobile touch targets are distinct
        pull=[0.03] * len(labels),
    ))

    annotations = []
    if center_label:
        annotations.append(dict(
            text=center_label,
            x=0.5, y=0.5,
            font=dict(size=12, family=FONT_SANS, color=TEXT_PRIMARY),
            showarrow=False,
        ))

    fig.update_layout(
        **_base_layout(
            height=260,
            margin=dict(t=8, b=8, l=8, r=8),
            showlegend=False,
            annotations=annotations,
            # Prevent label collision on mobile
            uniformtext=dict(minsize=8, mode="hide"),
        )
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# GROUPED BAR CHART  (50/30/20 rule comparison)
# ─────────────────────────────────────────────────────────────────────────────

def build_budget_comparison_bar(
    needs_pct: float,
    wants_pct: float,
    savings_pct: float,
) -> go.Figure:
    """
    Build a grouped bar chart comparing actual vs ideal 50/30/20 split.

    Mobile safety:
      - Reduced height (220px) fits on 375px-wide screens
      - Tick font size 10 to stay readable but compact
      - Legend positioned above, horizontal so it doesn't cut into chart area
      - bargap and bargroupgap tuned to avoid bars touching on mobile
    """
    categories = ["Needs", "Wants", "Savings"]
    actual_values = [needs_pct, wants_pct, savings_pct]
    ideal_values  = [50, 30, 20]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name="Your %",
        x=categories,
        y=actual_values,
        marker_color=COLOR_PRIMARY,
        marker_line_width=0,
        hovertemplate="%{x}: %{y:.0f}%<extra></extra>",
    ))

    fig.add_trace(go.Bar(
        name="50/30/20 ideal",
        x=categories,
        y=ideal_values,
        marker_color=TEXT_MUTED,
        marker_line_width=0,
        hovertemplate="%{x} ideal: %{y}%<extra></extra>",
        opacity=0.55,
    ))

    fig.update_layout(**_base_layout(
        barmode="group",
        height=220,
        margin=dict(t=30, b=10, l=8, r=8),
        legend=dict(
            bgcolor=_TRANSPARENT,
            orientation="h",
            y=1.15,
            x=0,
            font=dict(family=FONT_MONO, size=9, color=TEXT_MUTED),
        ),
        xaxis=dict(
            showgrid=False,
            tickfont=dict(family=FONT_SANS, size=10, color=TEXT_PRIMARY),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=BG_BORDER,
            ticksuffix="%",
            tickfont=dict(family=FONT_MONO, size=9, color=TEXT_MUTED),
            range=[0, max(max(actual_values), 55) + 5],  # stable y-axis range
        ),
        bargap=0.30,
        bargroupgap=0.08,
    ))
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# PALETTE CONSTANTS  (used when building charts)
# ─────────────────────────────────────────────────────────────────────────────

#: Standard colour rotation for category donuts
CATEGORY_COLOUR_PALETTE = [
    COLOR_PRIMARY, COLOR_TEAL, COLOR_AMBER, COLOR_PURPLE, COLOR_RED,
    COLOR_LGREEN, COLOR_SLATE, "#0E7C7B", "#B7791F", "#7C3AED",
    "#3DA968", "#C53929", "#6B7280", "#16794D",
]

#: Colours mapped to each portfolio asset class
PORTFOLIO_ASSET_COLOURS = {
    "Cash":        COLOR_TEAL,
    "Bonds":       COLOR_PURPLE,
    "Equity ETFs": COLOR_PRIMARY,
    "Stocks":      COLOR_AMBER,
    "Property":    COLOR_LGREEN,
    "Crypto":      COLOR_RED,
}

#: Brand colours per risk tier
TIER_COLOURS = {
    "Defensive":    COLOR_TEAL,
    "Conservative": COLOR_GREEN,
    "Balanced":     COLOR_PRIMARY,
    "Growth":       COLOR_AMBER,
    "Aggressive":   COLOR_RED,
}

TIER_BG_COLOURS = {
    "Defensive":    COLOR_TEAL_BG,
    "Conservative": COLOR_GREEN_BG,
    "Balanced":     COLOR_PRIMARY_BG,
    "Growth":       COLOR_AMBER_BG,
    "Aggressive":   COLOR_RED_BG,
}

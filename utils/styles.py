"""
utils/styles.py
===============
Design tokens (colours, fonts, spacing) and UI helper components.

All raw colour hex values live here as module-level constants so they
are imported and used consistently across the app.  Never hard-code a
hex value elsewhere — import from this module instead.

UI helper functions (note, section_header, metric_card, etc.) render
styled HTML fragments via st.markdown.  They accept only the data they
need and have no side effects beyond that single render call.
"""

import streamlit as st


# ─────────────────────────────────────────────────────────────────────────────
# COLOUR PALETTE  (light-green brand)
# ─────────────────────────────────────────────────────────────────────────────

# Backgrounds
BG_PAGE   = "#EAF5EC"   # page / outermost background
BG_CARD   = "#FFFFFF"   # card / surface background
BG_BORDER = "#CBE2D2"   # card borders and dividers

# Text
TEXT_PRIMARY = "#10241A"  # headings and body copy
TEXT_MUTED   = "#54695E"  # labels, captions, secondary text
TEXT_DIM     = "#95AC9E"  # disabled / very secondary text

# Brand – green
COLOR_PRIMARY    = "#16794D"
COLOR_PRIMARY_BG = "#E0F2E7"
COLOR_PRIMARY_DK = "#0E5C39"
COLOR_LGREEN     = "#3DA968"
COLOR_LGREEN_BG  = "#EAF6EE"

# Semantic colours
COLOR_GREEN      = "#16794D"
COLOR_GREEN_BG   = "#E0F2E7"
COLOR_AMBER      = "#B7791F"
COLOR_AMBER_BG   = "#FBF3E2"
COLOR_RED        = "#C53929"
COLOR_RED_BG     = "#FBEAE7"
COLOR_PURPLE     = "#7C3AED"
COLOR_PURPLE_BG  = "#F1ECFC"
COLOR_TEAL       = "#0E7C7B"
COLOR_TEAL_BG    = "#DFF2F1"
COLOR_SLATE      = "#6B7280"
COLOR_SLATE_BG   = "#F2F4F7"

# ─────────────────────────────────────────────────────────────────────────────
# TYPOGRAPHY
# ─────────────────────────────────────────────────────────────────────────────

FONT_SANS = "'Plus Jakarta Sans', system-ui, sans-serif"
FONT_MONO = "'JetBrains Mono', 'Fira Code', monospace"


# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────────────────────────────────────────

def inject_global_css(is_mobile: bool = False) -> None:
    """
    Inject the full application stylesheet once per page render.
    Must be called at the top of every page before any other st calls.
    """
    h_pad  = "1.2rem 1.2rem 1.1rem" if is_mobile else "1.6rem 2rem 1.4rem"
    b_pad  = "0 0.7rem 3rem"         if is_mobile else "0 1.6rem 3rem"
    tab_sz = "0.85rem"               if is_mobile else "0.98rem"
    tab_pd = "10px 13px"             if is_mobile else "13px 22px"

    st.markdown(f"""
    <style>
    /* ── Fonts ─────────────────────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

    /* ── Base reset ─────────────────────────────────────────────────────── */
    html, body, .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"] {{
        background: {BG_PAGE} !important;
        font-family: {FONT_SANS};
        color: {TEXT_PRIMARY} !important;
    }}

    /* Force dark text everywhere Streamlit injects its own colour */
    .stApp, .stApp p, .stApp label, .stApp li,
    [data-testid="stMarkdownContainer"],
    [data-testid="stWidgetLabel"] {{
        color: {TEXT_PRIMARY};
    }}

    .block-container {{
        padding: {b_pad};
        max-width: 1140px;
    }}

    /* Hide Streamlit chrome */
    #MainMenu, footer, header {{ visibility: hidden; }}

    /* ── Hide +/- spinner buttons on ALL number inputs ──────────────── */
    input[type=number]::-webkit-inner-spin-button,
    input[type=number]::-webkit-outer-spin-button {{
        -webkit-appearance: none !important;
        margin: 0 !important;
    }}
    input[type=number] {{ -moz-appearance: textfield !important; }}
    [data-testid="stNumberInput"] button,
    [data-testid="stNumberInput"] [data-testid="stNumberInputStepDown"],
    [data-testid="stNumberInput"] [data-testid="stNumberInputStepUp"] {{
        display: none !important;
    }}
    [data-testid="stNumberInput"] > div {{
        border: none !important;
        box-shadow: none !important;
    }}
    .stDeployButton {{ display: none !important; }}
    * {{ box-sizing: border-box; }}

    /* ── Headings ───────────────────────────────────────────────────────── */
    h1, h2, h3, h4 {{
        font-family: {FONT_SANS} !important;
        font-weight: 700 !important;
        color: {TEXT_PRIMARY} !important;
        margin: 0 !important;
    }}

    /* ── Layout gaps ────────────────────────────────────────────────────── */
    [data-testid="stVerticalBlock"] {{ gap: 0.55rem !important; }}
    [data-testid="stVerticalBlockBorderWrapper"] {{ border-radius: 12px !important; }}

    /* ── Tab navigation (visually distinct pill-style tabs) ─────────────── */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 5px;
        border-bottom: 2px solid {BG_BORDER};
        background: transparent;
        padding: 0;
        flex-wrap: wrap;
    }}
    .stTabs [data-baseweb="tab"] {{
        font-family: {FONT_SANS};
        font-size: {tab_sz};
        text-transform: none;
        color: {TEXT_MUTED};
        background: transparent;
        border: none;
        font-weight: 600;
        border-bottom: 3px solid transparent;
        padding: {tab_pd};
        border-radius: 10px 10px 0 0;
        transition: all .15s ease;
    }}
    .stTabs [data-baseweb="tab"]:hover {{
        color: {COLOR_PRIMARY} !important;
        background: {COLOR_PRIMARY_BG} !important;
    }}
    .stTabs [aria-selected="true"] {{
        color: {COLOR_PRIMARY} !important;
        border-bottom: 3px solid {COLOR_PRIMARY} !important;
        background: {COLOR_PRIMARY_BG} !important;
        font-weight: 700 !important;
    }}
    .stTabs [data-baseweb="tab-highlight"] {{ display: none !important; }}
    .stTabs [data-baseweb="tab-panel"] {{
        padding-top: 1.1rem;
        background: transparent;
    }}

    /* ── Number inputs ──────────────────────────────────────────────────── */
    div[data-testid="stNumberInput"] label,
    div[data-testid="stSelectbox"] label {{
        font-family: {FONT_SANS} !important;
        font-size: 0.78rem !important;
        text-transform: none !important;
        color: {TEXT_MUTED} !important;
        font-weight: 500 !important;
    }}
    .stNumberInput input {{
        background: {BG_CARD} !important;
        border: 1px solid {BG_BORDER} !important;
        border-radius: 8px !important;
        color: {TEXT_PRIMARY} !important;
        font-family: {FONT_MONO} !important;
        font-size: 0.92rem !important;
        padding: 7px 11px !important;
    }}
    .stNumberInput input:focus {{
        border-color: {COLOR_PRIMARY} !important;
        box-shadow: 0 0 0 3px rgba(22,121,77,0.15) !important;
        outline: none !important;
    }}
    .stNumberInput button {{
        background: {BG_CARD} !important;
        border-color: {BG_BORDER} !important;
    }}

    /* ── Text inputs ────────────────────────────────────────────────────── */
    .stTextInput input {{
        background: {BG_CARD} !important;
        border: 1px solid {BG_BORDER} !important;
        border-radius: 8px !important;
        color: {TEXT_PRIMARY} !important;
        font-family: {FONT_SANS} !important;
        font-size: 0.92rem !important;
        padding: 10px 13px !important;
    }}
    .stTextInput input:focus {{
        border-color: {COLOR_PRIMARY} !important;
        box-shadow: 0 0 0 3px rgba(22,121,77,0.15) !important;
        outline: none !important;
    }}
    div[data-testid="stTextInput"] label {{
        font-family: {FONT_SANS} !important;
        font-size: 0.78rem !important;
        color: {TEXT_MUTED} !important;
        font-weight: 500 !important;
    }}

    /* ── Radio buttons ──────────────────────────────────────────────────── */
    div[data-testid="stRadio"] *,
    [data-testid="stRadio"] label * {{
        color: {TEXT_PRIMARY} !important;
    }}
    div[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p {{
        color: {TEXT_PRIMARY} !important;
        font-family: {FONT_SANS} !important;
        font-size: 0.88rem !important;
        margin: 0 !important;
        line-height: 1.4 !important;
    }}
    div[data-testid="stRadio"] [role="radiogroup"] > label {{
        padding: 6px 10px;
        border-radius: 7px;
        margin-bottom: 2px;
        transition: background .12s ease;
        cursor: pointer;
    }}
    div[data-testid="stRadio"] [role="radiogroup"] > label:hover {{
        background: {COLOR_PRIMARY_BG};
    }}
    div[data-testid="stRadio"] > label {{
        font-family: {FONT_SANS} !important;
        font-size: 0.78rem !important;
        text-transform: none !important;
        color: {TEXT_MUTED} !important;
        font-weight: 500 !important;
    }}

    /* ── Primary button ─────────────────────────────────────────────────── */
    .stButton > button {{
        background: {COLOR_PRIMARY} !important;
        color: #fff !important;
        border: none !important;
        border-radius: 8px !important;
        font-family: {FONT_SANS} !important;
        font-size: 0.93rem !important;
        font-weight: 600 !important;
        padding: 10px 26px !important;
        box-shadow: 0 3px 12px rgba(22,121,77,0.30) !important;
        transition: all .15s !important;
        width: 100%;
        min-height: 44px;  /* accessibility: minimum touch target */
    }}
    .stButton > button:hover {{
        background: {COLOR_PRIMARY_DK} !important;
        transform: translateY(-1px) !important;
    }}

    /* ── Selectbox ──────────────────────────────────────────────────────── */
    .stSelectbox > div > div {{
        background: {BG_CARD} !important;
        border: 1px solid {BG_BORDER} !important;
        border-radius: 8px !important;
        font-family: {FONT_SANS} !important;
    }}
    [role="listbox"] *, [role="option"] {{
        background: {BG_CARD} !important;
        color: {TEXT_PRIMARY} !important;
    }}

    /* ── Divider ────────────────────────────────────────────────────────── */
    hr {{
        border: none;
        border-top: 1px solid {BG_BORDER};
        margin: 0.8rem 0;
    }}

    /* ── Data editor (expense table) ────────────────────────────────────── */
    [data-testid="stDataEditor"] {{
        border: 1px solid {BG_BORDER} !important;
        border-radius: 10px !important;
        overflow: hidden;
    }}

    /* ── Auth page card ─────────────────────────────────────────────────── */
    .auth-card {{
        background: {BG_CARD};
        border: 1px solid {BG_BORDER};
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 4px 24px rgba(14,92,57,0.10);
        max-width: 480px;
        margin: 0 auto;
    }}
    </style>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# REUSABLE UI COMPONENTS
# ─────────────────────────────────────────────────────────────────────────────

def render_app_header(is_mobile: bool = False, show_logout: bool = False) -> None:
    """
    Render the top application header bar.
    Includes brand logo, tagline, and optional logout button.
    """
    title_size  = "1.45rem" if is_mobile else "1.9rem"
    sub_size    = "0.78rem" if is_mobile else "0.9rem"
    logo_size   = "40px"    if is_mobile else "48px"
    logo_font   = "1.3rem"  if is_mobile else "1.6rem"
    margin_side = "-0.7rem" if is_mobile else "-1.6rem"
    hero_pad    = "1.2rem 1.2rem 1.1rem" if is_mobile else "1.6rem 2rem 1.4rem"

    logo_html = (
        f"<div style='width:{logo_size};height:{logo_size};border-radius:13px;"
        f"background:rgba(255,255,255,0.18);border:1px solid rgba(255,255,255,0.4);"
        f"display:flex;align-items:center;justify-content:center;"
        f"font-family:{FONT_SANS};font-size:{logo_font};font-weight:800;color:#fff;'>S</div>"
    )

    st.markdown(
        f"<div style='background:{COLOR_PRIMARY};border-radius:0 0 20px 20px;"
        f"padding:{hero_pad};margin:0 {margin_side} 1.2rem;"
        f"box-shadow:0 4px 16px rgba(14,92,57,0.18);'>"
        f"<div style='display:flex;align-items:center;gap:13px;'>{logo_html}"
        f"<div>"
        f"<div style='font-family:{FONT_SANS};font-size:{title_size};font-weight:800;"
        f"color:#fff;letter-spacing:-0.02em;line-height:1;'>Seralung Finance</div>"
        f"<div style='font-family:{FONT_SANS};font-size:{sub_size};"
        f"color:rgba(255,255,255,0.9);margin-top:4px;font-weight:500;'>"
        f"Understand Risk. Invest with Confidence.</div>"
        f"</div></div></div>",
        unsafe_allow_html=True,
    )

    # Disclaimer + logout row
    col_disc, col_logout = st.columns([6, 1])
    with col_disc:
        st.markdown(
            f"<div style='font-family:{FONT_SANS};font-size:0.78rem;color:{TEXT_MUTED};padding:4px 0 8px;'>"
            f"<span style='background:{COLOR_PRIMARY_BG};color:{COLOR_PRIMARY_DK};"
            f"font-weight:600;padding:3px 9px;border-radius:5px;'>Educational only</span>"
            f"&nbsp; Not personal financial advice — consult a licensed adviser before investing.</div>",
            unsafe_allow_html=True,
        )
    if show_logout:
        with col_logout:
            if st.button("Log out", key="btn_logout"):
                # Clear all session state and return to auth page
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()


def render_info_banner(message: str, kind: str = "info") -> None:
    """
    Render a coloured info/warning/success/alert banner.

    Parameters
    ----------
    message : str   HTML-safe message string
    kind    : str   One of "info" | "good" | "warn" | "alert"
    """
    colour_map = {
        "info":  (COLOR_PRIMARY_BG, COLOR_PRIMARY),
        "good":  (COLOR_GREEN_BG,   COLOR_GREEN),
        "warn":  (COLOR_AMBER_BG,   COLOR_AMBER),
        "alert": (COLOR_RED_BG,     COLOR_RED),
    }
    bg, accent = colour_map.get(kind, colour_map["info"])

    st.markdown(
        f"<div style='background:{bg};border-left:3px solid {accent};"
        f"border-radius:0 7px 7px 0;padding:9px 13px;margin:5px 0;"
        f"font-family:{FONT_SANS};font-size:0.88rem;color:{TEXT_PRIMARY};line-height:1.55;'>"
        f"{message}</div>",
        unsafe_allow_html=True,
    )


def render_section_header(label: str, accent_colour: str = COLOR_PRIMARY) -> None:
    """
    Render a horizontal section divider with a label.
    Used to separate content blocks within a tab.
    """
    st.markdown(
        f"<div style='display:flex;align-items:center;gap:10px;margin:18px 0 9px;'>"
        f"<span style='font-family:{FONT_SANS};font-size:0.78rem;letter-spacing:0.04em;"
        f"text-transform:uppercase;color:{accent_colour};white-space:nowrap;font-weight:700;'>"
        f"{label}</span>"
        f"<div style='flex:1;height:1px;background:{BG_BORDER};'></div></div>",
        unsafe_allow_html=True,
    )


def render_metric_card(
    label: str,
    value: str,
    subtitle: str = "",
    accent: str = COLOR_PRIMARY,
    bg: str = BG_CARD,
) -> None:
    """
    Render a single KPI metric card.
    Place inside st.columns() for a row of cards.
    """
    st.markdown(
        f"<div style='background:{bg};border:1px solid {BG_BORDER};"
        f"border-top:3px solid {accent};border-radius:0 0 10px 10px;"
        f"padding:12px 14px;min-width:0;height:100%;'>"
        f"<div style='font-family:{FONT_SANS};font-size:0.72rem;color:{TEXT_MUTED};"
        f"font-weight:500;margin-bottom:5px;overflow:hidden;text-overflow:ellipsis;"
        f"white-space:nowrap;'>{label}</div>"
        f"<div style='font-family:{FONT_SANS};font-size:1.35rem;color:{accent};"
        f"font-weight:700;line-height:1.2;word-break:break-word;'>{value}</div>"
        f"<div style='font-family:{FONT_SANS};font-size:0.72rem;color:{TEXT_MUTED};"
        f"margin-top:3px;line-height:1.4;'>{subtitle}</div></div>",
        unsafe_allow_html=True,
    )


def render_action_item(
    rank: int,
    title: str,
    description: str,
    kind: str = "info",
) -> None:
    """
    Render a single prioritised action item card in the Action Plan tab.

    Parameters
    ----------
    rank        : int   Display number (1, 2, 3 …)
    title       : str   Short action title
    description : str   Longer explanation
    kind        : str   "alert" | "warn" | "info" | "good"
    """
    colour_map = {
        "alert": (COLOR_RED_BG,     COLOR_RED),
        "warn":  (COLOR_AMBER_BG,   COLOR_AMBER),
        "info":  (COLOR_PRIMARY_BG, COLOR_PRIMARY),
        "good":  (COLOR_GREEN_BG,   COLOR_GREEN),
    }
    tag_map = {
        "alert": "Do first",
        "warn":  "Important",
        "info":  "Consider",
        "good":  "On track",
    }
    bg, accent = colour_map.get(kind, colour_map["info"])
    tag = tag_map.get(kind, "")

    st.markdown(
        f"<div style='background:{BG_CARD};border:1px solid {BG_BORDER};"
        f"border-left:3px solid {accent};border-radius:0 12px 12px 0;"
        f"padding:13px 16px;margin-bottom:8px;'>"
        f"<div style='display:flex;align-items:center;gap:10px;margin-bottom:4px;flex-wrap:wrap;'>"
        f"<span style='background:{accent};color:#fff;font-family:{FONT_SANS};font-size:0.8rem;"
        f"font-weight:800;width:24px;height:24px;border-radius:7px;display:inline-flex;"
        f"align-items:center;justify-content:center;flex-shrink:0;'>{rank}</span>"
        f"<span style='background:{bg};color:{accent};font-family:{FONT_SANS};font-size:0.62rem;"
        f"font-weight:700;padding:2px 9px;border-radius:20px;text-transform:uppercase;"
        f"letter-spacing:0.03em;'>{tag}</span>"
        f"<span style='font-family:{FONT_SANS};font-size:1rem;font-weight:700;"
        f"color:{TEXT_PRIMARY};'>{title}</span></div>"
        f"<div style='font-family:{FONT_SANS};font-size:0.88rem;color:{TEXT_MUTED};"
        f"line-height:1.55;padding-left:34px;'>{description}</div></div>",
        unsafe_allow_html=True,
    )

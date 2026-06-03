"""
pages/auth.py
=============
Authentication pages — each "page" is a distinct full-screen layout.

Routes (via session state):
  auth_mode = "home"     → split hero landing
  auth_mode = "login"    → dedicated sign-in page
  auth_mode = "register" → dedicated create account page
  auth_mode = "guest"    → 3-step guest quick-check

Design rules:
  - No hardcoded 0s — number inputs use value=None with placeholder text
  - No +/- spinner buttons on number inputs
  - Decimal values allowed on all numeric fields
  - Consistent card/form styling across login and register pages
  - Health score result uses red→amber→green gradient colour scale
  - All labels sit above their fields with consistent spacing
"""

from __future__ import annotations
import streamlit as st

from utils.styles import (
    inject_global_css, render_info_banner,
    BG_PAGE, BG_CARD, BG_BORDER,
    TEXT_PRIMARY, TEXT_MUTED,
    COLOR_PRIMARY, COLOR_PRIMARY_BG, COLOR_PRIMARY_DK,
    COLOR_GREEN, COLOR_GREEN_BG,
    COLOR_AMBER, COLOR_AMBER_BG,
    COLOR_RED, COLOR_RED_BG,
    COLOR_TEAL, COLOR_TEAL_BG,
    FONT_SANS, FONT_MONO,
)
from utils.calculations import (
    RISK_QUESTIONS,
    calculate_quiz_score, get_risk_tolerance_profile,
    calculate_guest_budget_summary, calculate_financial_health_score,
    get_health_rating, calculate_risk_capacity,
)
from utils.user_store import create_user, verify_login, get_user_profile


# ─────────────────────────────────────────────────────────────────────────────
# SHARED CSS  (injected on every auth page render)
# ─────────────────────────────────────────────────────────────────────────────

def _inject_auth_css() -> None:
    """
    Inject auth-specific CSS.

    Key rules:
    - Hides the Streamlit number-input +/- spinner buttons entirely.
    - Accepts decimal input via step="any" on number fields.
    - Consistent card, label, input, and button styling across all auth pages.
    - Error and success inline banners.
    """
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    /* ── Page base ──────────────────────────────────────────────────────── */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
        background: {BG_PAGE} !important;
        font-family: {FONT_SANS};
        color: {TEXT_PRIMARY};
    }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    .stDeployButton {{ display: none !important; }}

    /* ── Block container: clean padding ────────────────────────────────── */
    .block-container {{
        padding: 2rem 1.5rem 3rem !important;
        max-width: 1100px;
    }}

    /* ── HIDE +/- spinner buttons on ALL number inputs ──────────────────
       This targets every browser vendor prefix so it works everywhere.   */
    input[type=number]::-webkit-inner-spin-button,
    input[type=number]::-webkit-outer-spin-button {{
        -webkit-appearance: none !important;
        margin: 0 !important;
    }}
    input[type=number] {{
        -moz-appearance: textfield !important;
    }}
    /* Also hide Streamlit's own +/- button divs */
    [data-testid="stNumberInput"] button,
    [data-testid="stNumberInput"] [data-testid="stNumberInputStepDown"],
    [data-testid="stNumberInput"] [data-testid="stNumberInputStepUp"] {{
        display: none !important;
    }}
    [data-testid="stNumberInput"] > div {{
        border: none !important;
        box-shadow: none !important;
    }}

    /* ── Shared text input style ────────────────────────────────────────── */
    .stTextInput input,
    .stNumberInput input {{
        height: 48px !important;
        border: 1.5px solid {BG_BORDER} !important;
        border-radius: 10px !important;
        font-size: 0.95rem !important;
        padding: 0 14px !important;
        background: #fff !important;
        color: {TEXT_PRIMARY} !important;
        font-family: {FONT_SANS} !important;
        width: 100% !important;
        box-sizing: border-box !important;
        transition: border-color .15s, box-shadow .15s !important;
    }}
    .stTextInput input:focus,
    .stNumberInput input:focus {{
        border-color: {COLOR_PRIMARY} !important;
        box-shadow: 0 0 0 3px rgba(22,121,77,0.12) !important;
        outline: none !important;
    }}
    .stTextInput input::placeholder,
    .stNumberInput input::placeholder {{
        color: {TEXT_MUTED};
        opacity: 0.55;
    }}

    /* Hide Streamlit's auto-generated widget labels (we render our own) */
    div[data-testid="stTextInput"] label,
    div[data-testid="stNumberInput"] label {{
        display: none !important;
    }}

    /* ── Primary button ─────────────────────────────────────────────────── */
    .stButton > button {{
        background: {COLOR_PRIMARY} !important;
        color: #fff !important;
        border: none !important;
        border-radius: 10px !important;
        font-family: {FONT_SANS} !important;
        font-size: 0.95rem !important;
        font-weight: 700 !important;
        height: 48px !important;
        width: 100% !important;
        box-shadow: 0 3px 12px rgba(22,121,77,0.25) !important;
        transition: background .15s, transform .1s !important;
        letter-spacing: 0.01em;
    }}
    .stButton > button:hover {{
        background: {COLOR_PRIMARY_DK} !important;
        transform: translateY(-1px) !important;
    }}

    /* ── Auth card container ────────────────────────────────────────────── */
    .auth-card {{
        background: {BG_CARD};
        border: 1px solid {BG_BORDER};
        border-radius: 16px;
        padding: 2rem 2rem 1.6rem;
        box-shadow: 0 4px 24px rgba(14,92,57,0.08);
    }}

    /* ── Field label ────────────────────────────────────────────────────── */
    .f-label {{
        font-family: {FONT_SANS};
        font-size: 0.78rem;
        font-weight: 600;
        color: {TEXT_MUTED};
        margin-bottom: 5px;
        margin-top: 14px;
        display: block;
        letter-spacing: 0.01em;
    }}
    .f-label:first-child {{ margin-top: 0; }}

    /* ── Inline error banner ────────────────────────────────────────────── */
    .auth-error {{
        background: {COLOR_RED_BG};
        border: 1px solid {COLOR_RED};
        border-radius: 8px;
        padding: 10px 14px;
        font-family: {FONT_SANS};
        font-size: 0.84rem;
        color: {COLOR_RED};
        margin: 10px 0 4px;
        display: flex;
        align-items: center;
        gap: 8px;
        line-height: 1.4;
    }}

    /* ── Or divider ─────────────────────────────────────────────────────── */
    .or-divider {{
        display: flex;
        align-items: center;
        gap: 10px;
        margin: 16px 0;
        font-family: {FONT_SANS};
        font-size: 0.78rem;
        color: {TEXT_MUTED};
    }}
    .or-divider::before, .or-divider::after {{
        content: '';
        flex: 1;
        height: 1px;
        background: {BG_BORDER};
    }}

    /* ── Gradient health score bar ──────────────────────────────────────── */
    .health-gradient-bar {{
        height: 10px;
        border-radius: 5px;
        background: linear-gradient(90deg, #C53929 0%, #B7791F 40%, #16794D 100%);
        position: relative;
        margin: 8px 0 4px;
    }}

    /* ── Score breakdown bar ────────────────────────────────────────────── */
    .score-bar-wrap {{
        margin-bottom: 10px;
    }}
    .score-bar-track {{
        height: 7px;
        border-radius: 4px;
        background: rgba(0,0,0,0.07);
        overflow: hidden;
        margin-top: 4px;
    }}
    .score-bar-fill {{
        height: 100%;
        border-radius: 4px;
        transition: width .4s ease;
    }}

    /* ── Radio buttons ──────────────────────────────────────────────────── */
    div[data-testid="stRadio"] label,
    div[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p {{
        color: {TEXT_PRIMARY} !important;
        font-family: {FONT_SANS} !important;
        font-size: 0.88rem !important;
    }}
    div[data-testid="stRadio"] > label {{ display: none !important; }}

    /* ── Step progress pills ────────────────────────────────────────────── */
    .step-row {{
        display: flex;
        align-items: center;
        margin-bottom: 1.8rem;
    }}
    .step-circle {{
        width: 34px; height: 34px;
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-family: {FONT_SANS}; font-size: 0.85rem; font-weight: 700;
        flex-shrink: 0;
    }}
    .step-line {{
        height: 2px; flex: 1;
    }}
    .step-label {{
        font-family: {FONT_SANS}; font-size: 0.7rem;
        text-align: center; margin-top: 5px;
    }}
    </style>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def render_auth_page() -> None:
    """Route to the correct auth sub-page."""
    is_mobile = st.session_state.get("is_mobile", False)
    inject_global_css(is_mobile)
    _inject_auth_css()

    for key in ("auth_mode", "auth_error", "auth_success"):
        if key not in st.session_state:
            st.session_state[key] = "home" if key == "auth_mode" else ""

    mode = st.session_state["auth_mode"]
    if   mode == "home":     _render_home_page(is_mobile)
    elif mode == "login":    _render_login_page(is_mobile)
    elif mode == "register": _render_register_page(is_mobile)
    elif mode == "guest":    _render_guest_flow(is_mobile)


# ─────────────────────────────────────────────────────────────────────────────
# NAVIGATION HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _navigate(mode: str) -> None:
    st.session_state["auth_mode"]   = mode
    st.session_state["auth_error"]  = ""
    st.session_state["auth_success"] = ""
    st.rerun()


def _show_error(msg: str) -> None:
    st.markdown(
        f"<div class='auth-error'>"
        f"<svg width='15' height='15' viewBox='0 0 16 16' fill='none'>"
        f"<circle cx='8' cy='8' r='7' stroke='{COLOR_RED}' stroke-width='1.5'/>"
        f"<path d='M8 5v3.5' stroke='{COLOR_RED}' stroke-width='1.5' stroke-linecap='round'/>"
        f"<circle cx='8' cy='11' r='.75' fill='{COLOR_RED}'/>"
        f"</svg>{msg}</div>",
        unsafe_allow_html=True,
    )


def _field_label(text: str, hint: str = "") -> None:
    """Render a consistent field label above an input."""
    hint_html = f" <span style='font-weight:400;opacity:0.65;'>— {hint}</span>" if hint else ""
    st.markdown(f"<div class='f-label'>{text}{hint_html}</div>", unsafe_allow_html=True)


def _nav_bar(title: str) -> None:
    """Minimal back-arrow nav bar shown on login / register / guest pages."""
    c1, c2 = st.columns([0.12, 3])
    with c1:
        if st.button("←", key=f"back_{title}"):
            _navigate("home")
    with c2:
        st.markdown(
            f"<div style='padding-top:9px;font-family:{FONT_SANS};"
            f"font-size:0.8rem;font-weight:600;color:{TEXT_MUTED};'>{title}</div>",
            unsafe_allow_html=True,
        )
    st.markdown(f"<hr style='border:none;border-top:1px solid {BG_BORDER};margin:0 0 1.6rem;'>",
                unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# HOME PAGE  — split layout (hero left / form right)
# ─────────────────────────────────────────────────────────────────────────────

def _render_home_page(is_mobile: bool) -> None:
    """
    Facebook-style split: green hero panel on the left, sign-in form on the right.
    Uses CSS flex on a single HTML block so both panels share one layout context
    — this survives Streamlit Cloud's iframe sandbox where position:fixed breaks.
    """
    features = [
        ("S", "Smart budget tracking",     "Track every expense by category in real time."),
        ("H", "Financial health score",    "A single 0–100 score built from your real numbers."),
        ("P", "Investment recommendation", "Five portfolios matched to your risk profile."),
        ("A", "Prioritised action plan",   "What to fix, in what order, with dollar amounts."),
    ]
    feature_html = ""
    for icon, title, desc in features:
        feature_html += (
            f'<div style="display:flex;align-items:flex-start;gap:14px;margin-bottom:20px;">'
            f'<div style="min-width:38px;height:38px;border-radius:9px;'
            f'background:rgba(255,255,255,0.13);border:1px solid rgba(255,255,255,0.2);'
            f'display:flex;align-items:center;justify-content:center;'
            f'font-family:{FONT_SANS};font-size:0.88rem;font-weight:800;color:#fff;">{icon}</div>'
            f'<div><div style="font-family:{FONT_SANS};font-weight:700;color:#fff;'
            f'font-size:0.92rem;margin-bottom:2px;">{title}</div>'
            f'<div style="font-family:{FONT_SANS};font-size:0.8rem;'
            f'color:rgba(255,255,255,0.62);line-height:1.45;">{desc}</div>'
            f'</div></div>'
        )

    st.markdown(f"""
    <style>
    [data-testid="stAppViewContainer"],[data-testid="stMain"]{{
        padding:0!important;margin:0!important;overflow-x:hidden!important;
    }}
    .sf-split{{display:flex;min-height:100vh;width:100%;}}
    .sf-hero{{
        flex:1.05;
        background:linear-gradient(150deg,{COLOR_PRIMARY} 0%,{COLOR_PRIMARY_DK} 100%);
        padding:3.5rem 3.2rem;display:flex;flex-direction:column;
        justify-content:center;min-height:100vh;
    }}
    .sf-right{{
        flex:0.95;background:{BG_CARD};min-height:100vh;
        display:flex;align-items:center;justify-content:center;
    }}
    .block-container{{
        background:{BG_CARD}!important;
        padding:2rem 2.5rem!important;
        max-width:440px!important;
        margin-left:auto!important;margin-right:auto!important;
        min-height:100vh!important;display:flex!important;
        flex-direction:column!important;justify-content:center!important;
    }}
    @media(max-width:700px){{
        .sf-hero{{display:none!important;}}
        .sf-split{{min-height:unset;}}
        .block-container{{padding:1.5rem 1.2rem!important;max-width:100%!important;min-height:unset!important;}}
    }}
    </style>
    <div class="sf-split">
        <div class="sf-hero">
            <div style="margin-bottom:2.2rem;">
                <div style="font-family:{FONT_SANS};font-size:2.5rem;font-weight:800;
                    color:#fff;line-height:1.05;letter-spacing:-0.03em;margin-bottom:10px;">
                    Seralung<br>Finance</div>
                <div style="font-family:{FONT_SANS};font-size:1rem;
                    color:rgba(255,255,255,0.8);line-height:1.65;">
                    Understand your finances.<br>Invest with confidence.</div>
            </div>
            {feature_html}
            <div style="font-family:{FONT_SANS};font-size:0.7rem;
                color:rgba(255,255,255,0.35);line-height:1.6;margin-top:1rem;">
                Educational only — not personal financial advice.<br>
                Consult a licensed adviser (AFSL) before investing.</div>
        </div>
        <div class="sf-right"></div>
    </div>
    """, unsafe_allow_html=True)

    if is_mobile:
        st.markdown(
            f"<div style='background:linear-gradient(135deg,{COLOR_PRIMARY},{COLOR_PRIMARY_DK});"
            f"padding:22px 20px 18px;border-radius:0 0 18px 18px;margin-bottom:1.5rem;'>"
            f"<div style='font-family:{FONT_SANS};font-size:1.5rem;font-weight:800;"
            f"color:#fff;'>Seralung Finance</div>"
            f"<div style='font-family:{FONT_SANS};font-size:0.83rem;"
            f"color:rgba(255,255,255,0.8);margin-top:3px;'>"
            f"Understand your finances. Invest with confidence.</div></div>",
            unsafe_allow_html=True,
        )
    _render_home_form()


def _render_home_form() -> None:
    """Sign-in form rendered in the right panel of the home split layout."""
    _, col, _ = st.columns([0.1, 3, 0.1])
    with col:
        st.markdown(
            f"<div style='font-family:{FONT_SANS};font-size:1.55rem;font-weight:800;"
            f"color:{TEXT_PRIMARY};letter-spacing:-0.02em;margin-bottom:3px;'>Sign in</div>"
            f"<div style='font-family:{FONT_SANS};font-size:0.88rem;color:{TEXT_MUTED};"
            f"margin-bottom:1.5rem;'>Access your financial dashboard</div>",
            unsafe_allow_html=True,
        )
        _field_label("Username")
        username = st.text_input("u", key="home_username", placeholder="Enter your username",
                                 label_visibility="collapsed")
        _field_label("Password")
        password = st.text_input("p", type="password", key="home_password",
                                 placeholder="Enter your password", label_visibility="collapsed")

        if st.session_state.get("auth_error"):
            _show_error(st.session_state["auth_error"])

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        if st.button("Sign in", key="btn_home_signin"):
            _handle_login(username, password)

        st.markdown("<div class='or-divider'>or</div>", unsafe_allow_html=True)
        if st.button("Create a free account", key="btn_home_register"):
            _navigate("register")

        st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
        if st.button("Check my financial health — no account needed", key="btn_home_guest"):
            _navigate("guest")

        st.markdown(
            f"<div style='font-family:{FONT_SANS};font-size:0.72rem;color:{TEXT_MUTED};"
            f"text-align:center;margin-top:12px;line-height:1.5;'>"
            f"Educational purposes only — not personal financial advice.</div>",
            unsafe_allow_html=True,
        )


# ─────────────────────────────────────────────────────────────────────────────
# LOGIN PAGE  — /login
# ─────────────────────────────────────────────────────────────────────────────

def _render_login_page(is_mobile: bool) -> None:
    """Dedicated sign-in page — centred card, consistent with register page."""
    _nav_bar("Sign In")
    _, col, _ = st.columns([1, 2, 1] if not is_mobile else [0.05, 3, 0.05])
    with col:
        # Brand mark
        st.markdown(
            f"<div style='text-align:center;margin-bottom:1.8rem;'>"
            f"<div style='display:inline-flex;width:52px;height:52px;border-radius:14px;"
            f"background:linear-gradient(135deg,{COLOR_PRIMARY},{COLOR_PRIMARY_DK});"
            f"align-items:center;justify-content:center;"
            f"font-family:{FONT_SANS};font-size:1.4rem;font-weight:800;color:#fff;"
            f"margin-bottom:12px;'>S</div><br>"
            f"<span style='font-family:{FONT_SANS};font-size:1.55rem;font-weight:800;"
            f"color:{TEXT_PRIMARY};'>Welcome back</span><br>"
            f"<span style='font-family:{FONT_SANS};font-size:0.88rem;color:{TEXT_MUTED};"
            f"margin-top:4px;display:block;'>Sign in to your account</span></div>",
            unsafe_allow_html=True,
        )
        st.markdown("<div class='auth-card'>", unsafe_allow_html=True)
        _field_label("Username")
        username = st.text_input("Username", key="login_username",
                                 placeholder="Your username", label_visibility="collapsed")
        _field_label("Password")
        password = st.text_input("Password", type="password", key="login_password",
                                 placeholder="Your password", label_visibility="collapsed")
        if st.session_state.get("auth_error"):
            _show_error(st.session_state["auth_error"])
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        if st.button("Sign in", key="btn_login_submit"):
            _handle_login(username, password)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
        if st.button("Don't have an account? Create one →", key="btn_login_to_reg"):
            _navigate("register")


# ─────────────────────────────────────────────────────────────────────────────
# REGISTER PAGE  — /signup
# ─────────────────────────────────────────────────────────────────────────────

def _render_register_page(is_mobile: bool) -> None:
    """
    Dedicated create-account page.
    Uses identical card style, spacing, label style, and button as the login page
    so both pages feel like they belong to the same design system.
    """
    _nav_bar("Create Account")
    _, col, _ = st.columns([1, 2, 1] if not is_mobile else [0.05, 3, 0.05])
    with col:
        # Brand mark — identical to login page
        st.markdown(
            f"<div style='text-align:center;margin-bottom:1.8rem;'>"
            f"<div style='display:inline-flex;width:52px;height:52px;border-radius:14px;"
            f"background:linear-gradient(135deg,{COLOR_PRIMARY},{COLOR_PRIMARY_DK});"
            f"align-items:center;justify-content:center;"
            f"font-family:{FONT_SANS};font-size:1.4rem;font-weight:800;color:#fff;"
            f"margin-bottom:12px;'>S</div><br>"
            f"<span style='font-family:{FONT_SANS};font-size:1.55rem;font-weight:800;"
            f"color:{TEXT_PRIMARY};'>Create your account</span><br>"
            f"<span style='font-family:{FONT_SANS};font-size:0.88rem;color:{TEXT_MUTED};"
            f"margin-top:4px;display:block;'>Free forever — no credit card needed</span></div>",
            unsafe_allow_html=True,
        )
        st.markdown("<div class='auth-card'>", unsafe_allow_html=True)
        _field_label("Choose a username")
        username = st.text_input("Username", key="reg_username",
                                 placeholder="e.g. jane_smith", label_visibility="collapsed")
        _field_label("Create a password", "min. 6 characters")
        password = st.text_input("Password", type="password", key="reg_password",
                                 placeholder="At least 6 characters", label_visibility="collapsed")
        _field_label("Confirm password")
        password_confirm = st.text_input("Confirm", type="password", key="reg_confirm",
                                         placeholder="Repeat your password",
                                         label_visibility="collapsed")
        if st.session_state.get("auth_error"):
            _show_error(st.session_state["auth_error"])
        if st.session_state.get("auth_success"):
            st.markdown(
                f"<div style='background:{COLOR_GREEN_BG};border:1px solid {COLOR_GREEN};"
                f"border-radius:8px;padding:10px 14px;font-family:{FONT_SANS};"
                f"font-size:0.84rem;color:{COLOR_GREEN};margin:10px 0;'>"
                f"{st.session_state['auth_success']}</div>",
                unsafe_allow_html=True,
            )
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        if st.button("Create account", key="btn_reg_submit"):
            _handle_register(username, password, password_confirm)
        st.markdown(
            f"<div style='font-family:{FONT_SANS};font-size:0.72rem;color:{TEXT_MUTED};"
            f"margin-top:12px;text-align:center;line-height:1.5;'>"
            f"By creating an account you agree this is educational only.<br>"
            f"Not personal financial advice.</div>",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
        if st.button("Already have an account? Sign in →", key="btn_reg_to_login"):
            _navigate("login")


# ─────────────────────────────────────────────────────────────────────────────
# AUTH LOGIC
# ─────────────────────────────────────────────────────────────────────────────

def _handle_login(username: str, password: str) -> None:
    st.session_state["auth_error"] = ""
    if not username.strip():
        st.session_state["auth_error"] = "Please enter your username."; st.rerun(); return
    if not password:
        st.session_state["auth_error"] = "Please enter your password."; st.rerun(); return
    if verify_login(username, password):
        profile = get_user_profile(username)
        st.session_state.update({
            "is_authenticated":      True,
            "current_user":          username.lower().strip(),
            "user_income_primary":   profile.get("income_primary",   None),
            "user_income_secondary": profile.get("income_secondary", None),
            "user_savings":          profile.get("current_savings",  None),
            "user_expenses":         profile.get("expenses",         []),
            "next_expense_id":       profile.get("next_expense_id",  1),
            "auth_error":            "",
        })
        for i, ans in enumerate(profile.get("quiz_answers", [0]*10)):
            st.session_state[f"quiz_q{i+1}"] = ans
        st.rerun()
    else:
        st.session_state["auth_error"] = "Incorrect username or password. Please try again."
        st.rerun()


def _handle_register(username: str, password: str, password_confirm: str) -> None:
    st.session_state["auth_error"] = st.session_state["auth_success"] = ""
    username = username.strip()
    if not username:
        st.session_state["auth_error"] = "Please choose a username."; st.rerun(); return
    if len(username) < 3:
        st.session_state["auth_error"] = "Username must be at least 3 characters."; st.rerun(); return
    if len(password) < 6:
        st.session_state["auth_error"] = "Password must be at least 6 characters."; st.rerun(); return
    if password != password_confirm:
        st.session_state["auth_error"] = "Passwords do not match."; st.rerun(); return
    if not create_user(username, password):
        st.session_state["auth_error"] = f"Username '{username}' is already taken."; st.rerun(); return
    st.session_state.update({
        "is_authenticated": True, "current_user": username.lower(),
        "user_income_primary": None, "user_income_secondary": None,
        "user_savings": None, "user_expenses": [], "next_expense_id": 1,
        "auth_error": "",
    })
    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# GUEST QUICK-CHECK  — 3-step flow
# ─────────────────────────────────────────────────────────────────────────────

def _render_guest_flow(is_mobile: bool) -> None:
    _nav_bar("Quick Health Check")
    if "guest_step" not in st.session_state:
        st.session_state["guest_step"] = 1
    _render_progress_bar(st.session_state["guest_step"])
    step = st.session_state["guest_step"]
    if   step == 1: _guest_step1(is_mobile)
    elif step == 2: _guest_step2(is_mobile)
    elif step == 3: _guest_step3(is_mobile)


def _render_progress_bar(current: int) -> None:
    """3-step horizontal progress indicator."""
    labels = ["Your Finances", "10 Questions", "Your Results"]
    html = "<div class='step-row'>"
    for i, label in enumerate(labels, 1):
        active = (i == current)
        done   = (i < current)
        if active:
            cs = f"background:{COLOR_PRIMARY};color:#fff;border:2px solid {COLOR_PRIMARY};"
            ls = f"color:{COLOR_PRIMARY};font-weight:700;"
        elif done:
            cs = f"background:{COLOR_GREEN};color:#fff;border:2px solid {COLOR_GREEN};"
            ls = f"color:{COLOR_GREEN};font-weight:600;"
        else:
            cs = f"background:transparent;color:{TEXT_MUTED};border:2px solid {BG_BORDER};"
            ls = f"color:{TEXT_MUTED};"
        num = "✓" if done else str(i)
        html += (
            f"<div style='display:flex;flex-direction:column;align-items:center;gap:5px;flex:1;'>"
            f"<div class='step-circle' style='{cs}'>{num}</div>"
            f"<div class='step-label' style='{ls}'>{label}</div></div>"
        )
        if i < len(labels):
            lc = COLOR_GREEN if done else BG_BORDER
            html += f"<div class='step-line' style='background:{lc};margin-bottom:22px;'></div>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def _guest_step1(is_mobile: bool) -> None:
    """
    Step 1: income, rough expenses, savings.
    All inputs use value=None so fields appear blank (no hardcoded 0).
    step=any allows decimals; +/- buttons hidden via CSS.
    """
    _, col, _ = st.columns([1, 2.5, 1] if not is_mobile else [0.05, 3, 0.05])
    with col:
        st.markdown(
            f"<div style='font-family:{FONT_SANS};font-size:1.2rem;font-weight:800;"
            f"color:{TEXT_PRIMARY};margin-bottom:4px;'>Your financial snapshot</div>"
            f"<div style='font-family:{FONT_SANS};font-size:0.87rem;color:{TEXT_MUTED};"
            f"line-height:1.55;margin-bottom:1rem;'>"
            f"No detailed breakdown needed — just rough monthly numbers.</div>",
            unsafe_allow_html=True,
        )
        st.markdown("<div class='auth-card'>", unsafe_allow_html=True)

        _field_label("Monthly income after tax ($)")
        income = st.number_input("inc", min_value=0.0, step=None, value=None,
                                 placeholder="e.g. 5000.00",
                                 key="guest_monthly_income", label_visibility="collapsed",
                                 format="%.2f")

        _field_label("Rough total monthly expenses ($)", "rent, food, bills, everything")
        expenses = st.number_input("exp", min_value=0.0, step=None, value=None,
                                   placeholder="e.g. 3500.00",
                                   key="guest_rough_expenses", label_visibility="collapsed",
                                   format="%.2f")

        _field_label("Total cash savings ($)", "accessible savings + emergency fund")
        savings = st.number_input("sav", min_value=0.0, step=None, value=None,
                                  placeholder="e.g. 10000.00",
                                  key="guest_total_savings", label_visibility="collapsed",
                                  format="%.2f")

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        if st.button("Next: 10 Questions →", key="btn_g1"):
            if not income or income <= 0:
                _show_error("Please enter your monthly income to continue.")
            else:
                st.session_state["guest_step"] = 2; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


def _guest_step2(is_mobile: bool) -> None:
    """Step 2: 10 risk-tolerance questions with live profile preview."""
    st.markdown(
        f"<div style='font-family:{FONT_SANS};font-size:1.2rem;font-weight:800;"
        f"color:{TEXT_PRIMARY};margin-bottom:4px;'>10 quick questions</div>"
        f"<div style='font-family:{FONT_SANS};font-size:0.87rem;color:{TEXT_MUTED};"
        f"line-height:1.55;margin-bottom:1rem;'>"
        f"No right or wrong answers — be honest. Your profile updates live.</div>",
        unsafe_allow_html=True,
    )
    for i, (q_text, options) in enumerate(RISK_QUESTIONS):
        q_key = f"quiz_q{i+1}"
        with st.container(border=True):
            st.markdown(
                f"<div style='display:flex;gap:10px;align-items:flex-start;margin-bottom:8px;'>"
                f"<div style='background:{COLOR_PRIMARY_BG};color:{COLOR_PRIMARY};"
                f"font-family:{FONT_SANS};font-size:0.68rem;font-weight:700;"
                f"padding:3px 9px;border-radius:20px;flex-shrink:0;white-space:nowrap;'>"
                f"Q{i+1}/10</div>"
                f"<div style='font-family:{FONT_SANS};font-size:0.92rem;font-weight:600;"
                f"color:{TEXT_PRIMARY};line-height:1.4;'>{q_text}</div></div>",
                unsafe_allow_html=True,
            )
            sel = st.radio(q_text, options=list(range(len(options))),
                           format_func=lambda idx, o=options: o[idx],
                           index=st.session_state.get(q_key, 0),
                           key=f"gr_{q_key}", label_visibility="collapsed")
            st.session_state[q_key] = sel

    # Live preview strip
    answers = [st.session_state.get(f"quiz_q{i}", 0) for i in range(1, 11)]
    quiz_score = calculate_quiz_score(answers)
    name, level = get_risk_tolerance_profile(quiz_score)
    pmap = {
        "Conservative":            (COLOR_TEAL,    COLOR_TEAL_BG),
        "Moderately Conservative": (COLOR_GREEN,   COLOR_GREEN_BG),
        "Balanced":                (COLOR_PRIMARY, COLOR_PRIMARY_BG),
        "Growth":                  (COLOR_AMBER,   COLOR_AMBER_BG),
        "Aggressive":              (COLOR_RED,     COLOR_RED_BG),
    }
    pc, pb = pmap.get(name, (COLOR_PRIMARY, COLOR_PRIMARY_BG))
    pct = ((quiz_score - 10) / 30) * 100
    st.markdown(
        f"<div style='background:{pb};border:1px solid {BG_BORDER};"
        f"border-left:4px solid {pc};border-radius:0 10px 10px 0;padding:12px 16px;margin:12px 0;'>"
        f"<div style='font-family:{FONT_SANS};font-size:0.68rem;color:{TEXT_MUTED};"
        f"font-weight:700;letter-spacing:0.04em;margin-bottom:4px;'>LIVE PREVIEW</div>"
        f"<div style='font-family:{FONT_SANS};font-size:1.2rem;font-weight:800;color:{pc};'>"
        f"{name} <span style='font-size:0.82rem;font-weight:500;color:{TEXT_MUTED};'>"
        f"Level {level}/5</span></div>"
        f"<div style='height:5px;background:rgba(0,0,0,0.07);border-radius:3px;"
        f"margin-top:8px;overflow:hidden;'>"
        f"<div style='width:{pct:.0f}%;height:100%;background:{pc};border-radius:3px;'>"
        f"</div></div></div>",
        unsafe_allow_html=True,
    )
    bc, nc = st.columns(2)
    with bc:
        if st.button("← Back", key="btn_g2_back"): st.session_state["guest_step"] = 1; st.rerun()
    with nc:
        if st.button("See my results →", key="btn_g2_next"): st.session_state["guest_step"] = 3; st.rerun()


def _guest_step3(is_mobile: bool) -> None:
    """
    Step 3: health score + risk profile results.

    Health score display uses a red→amber→green gradient bar so users
    immediately understand where on the scale they sit without needing
    to read the label — matches the reference image (Image 2).
    """
    budget = calculate_guest_budget_summary(
        monthly_income  = float(st.session_state.get("guest_monthly_income") or 0),
        rough_expenses  = float(st.session_state.get("guest_rough_expenses")  or 0),
        current_savings = float(st.session_state.get("guest_total_savings")   or 0),
    )
    health_score, breakdown = calculate_financial_health_score(budget)
    rating_label, rating_colour, rating_bg = get_health_rating(health_score)

    answers = [st.session_state.get(f"quiz_q{i}", 0) for i in range(1, 11)]
    quiz_score = calculate_quiz_score(answers)
    profile_name, profile_level = get_risk_tolerance_profile(quiz_score)
    _, cap_level, cap_label = calculate_risk_capacity(budget)

    pmap = {
        "Conservative":            (COLOR_TEAL,    COLOR_TEAL_BG),
        "Moderately Conservative": (COLOR_GREEN,   COLOR_GREEN_BG),
        "Balanced":                (COLOR_PRIMARY, COLOR_PRIMARY_BG),
        "Growth":                  (COLOR_AMBER,   COLOR_AMBER_BG),
        "Aggressive":              (COLOR_RED,     COLOR_RED_BG),
    }
    pc, pb = pmap.get(profile_name, (COLOR_PRIMARY, COLOR_PRIMARY_BG))

    st.markdown(
        f"<div style='font-family:{FONT_SANS};font-size:1.2rem;font-weight:800;"
        f"color:{TEXT_PRIMARY};margin-bottom:1rem;'>Your results</div>",
        unsafe_allow_html=True,
    )

    left, right = st.columns(2, gap="medium")

    # ── Left: Health score card with gradient bar + breakdown ─────────────
    with left:
        # Marker position on the gradient bar (0–100 → 0–100%)
        marker_pct = health_score

        # Score breakdown HTML
        breakdown_html = ""
        for comp, (earned, maximum) in breakdown.items():
            bar_pct = earned / maximum * 100
            bar_col = COLOR_GREEN if bar_pct >= 70 else COLOR_AMBER if bar_pct >= 40 else COLOR_RED
            breakdown_html += (
                f"<div class='score-bar-wrap'>"
                f"<div style='display:flex;justify-content:space-between;"
                f"font-family:{FONT_SANS};font-size:0.78rem;'>"
                f"<span style='color:{TEXT_PRIMARY};'>{comp}</span>"
                f"<span style='color:{bar_col};font-weight:700;font-family:{FONT_MONO};'>"
                f"{earned}/{maximum}</span></div>"
                f"<div class='score-bar-track'>"
                f"<div class='score-bar-fill' style='width:{bar_pct:.0f}%;background:{bar_col};'>"
                f"</div></div></div>"
            )

        st.markdown(
            f"<div style='background:{BG_CARD};border:1px solid {BG_BORDER};"
            f"border-radius:16px;padding:20px;box-shadow:0 4px 20px rgba(0,0,0,0.06);'>"

            # Score number + label
            f"<div style='display:flex;align-items:flex-end;gap:10px;margin-bottom:6px;'>"
            f"<div style='font-family:{FONT_SANS};font-size:3.8rem;font-weight:800;"
            f"color:{rating_colour};line-height:1;'>{health_score}</div>"
            f"<div style='font-family:{FONT_SANS};font-size:0.82rem;color:{TEXT_MUTED};"
            f"margin-bottom:10px;'>/ 100</div></div>"

            # Rating badge
            f"<div style='display:inline-block;background:{rating_colour};color:#fff;"
            f"font-family:{FONT_SANS};font-size:0.78rem;font-weight:700;"
            f"padding:4px 14px;border-radius:20px;margin-bottom:14px;'>"
            f"{rating_label}</div>"

            # Gradient bar with marker
            f"<div style='font-family:{FONT_SANS};font-size:0.68rem;color:{TEXT_MUTED};"
            f"font-weight:600;letter-spacing:0.04em;margin-bottom:5px;'>HEALTH SCALE</div>"
            f"<div style='position:relative;margin-bottom:18px;'>"
            f"<div class='health-gradient-bar'></div>"
            # Marker pin
            f"<div style='position:absolute;top:-4px;left:{marker_pct}%;"
            f"transform:translateX(-50%);width:3px;height:18px;"
            f"background:{TEXT_PRIMARY};border-radius:2px;'></div>"
            f"<div style='display:flex;justify-content:space-between;"
            f"font-family:{FONT_MONO};font-size:0.62rem;color:{TEXT_MUTED};margin-top:3px;'>"
            f"<span>Poor</span><span>Fair</span><span>Good</span><span>Excellent</span></div>"
            f"</div>"

            # Score breakdown
            f"<div style='font-family:{FONT_SANS};font-size:0.68rem;color:{TEXT_MUTED};"
            f"font-weight:600;letter-spacing:0.04em;margin-bottom:8px;'>SCORE BREAKDOWN</div>"
            f"{breakdown_html}"
            f"</div>",
            unsafe_allow_html=True,
        )

    # ── Right: Risk profile + unlock gate ────────────────────────────────
    with right:
        st.markdown(
            f"<div style='background:{BG_CARD};border:1px solid {BG_BORDER};"
            f"border-radius:16px;padding:20px;box-shadow:0 4px 20px rgba(0,0,0,0.06);"
            f"margin-bottom:12px;'>"
            f"<div style='font-family:{FONT_SANS};font-size:0.68rem;font-weight:700;"
            f"color:{TEXT_MUTED};text-transform:uppercase;letter-spacing:0.05em;"
            f"margin-bottom:8px;'>Risk Profile</div>"
            f"<div style='font-family:{FONT_SANS};font-size:1.5rem;font-weight:800;"
            f"color:{pc};'>{profile_name}</div>"
            f"<div style='font-family:{FONT_SANS};font-size:0.82rem;color:{TEXT_MUTED};"
            f"margin-top:5px;'>Level {profile_level}/5</div>"
            f"<div style='height:1px;background:{BG_BORDER};margin:12px 0;'></div>"
            f"<div style='font-family:{FONT_SANS};font-size:0.82rem;color:{TEXT_MUTED};'>"
            f"Financial capacity: <strong style='color:{TEXT_PRIMARY};'>{cap_label}</strong>"
            f"</div></div>",
            unsafe_allow_html=True,
        )

        # Verdict banner
        if health_score >= 65:
            render_info_banner(
                f"<strong>Good foundation.</strong> Create an account to unlock your "
                f"full investment plan and action items.", "good")
        elif health_score >= 40:
            render_info_banner(
                f"<strong>Room to improve.</strong> Score {health_score}/100. "
                f"Create an account to see exactly what to fix and in what order.", "warn")
        else:
            render_info_banner(
                f"<strong>Attention needed.</strong> Score {health_score}/100. "
                f"A full action plan is waiting.", "alert")

        # Unlock gate
        st.markdown(
            f"<div style='background:{BG_CARD};border:1px solid {BG_BORDER};"
            f"border-radius:14px;padding:16px;margin-top:10px;'>"
            f"<div style='font-family:{FONT_SANS};font-size:0.95rem;font-weight:800;"
            f"color:{TEXT_PRIMARY};margin-bottom:10px;'>Unlock your full plan</div>"
            + "".join([
                f"<div style='font-family:{FONT_SANS};font-size:0.82rem;color:{TEXT_MUTED};"
                f"display:flex;gap:8px;margin-bottom:6px;'>"
                f"<span style='color:{COLOR_GREEN};font-weight:700;'>✓</span>{item}</div>"
                for item in [
                    "Per-expense budget tracking",
                    "Full health score breakdown",
                    "Portfolio recommendation",
                    "Prioritised action plan",
                ]
            ])
            + "</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
    cta, back = st.columns([2, 1])
    with cta:
        if st.button("Create free account →", key="btn_g3_signup"): _navigate("register")
    with back:
        if st.button("← Redo answers", key="btn_g3_redo"):
            st.session_state["guest_step"] = 1; st.rerun()

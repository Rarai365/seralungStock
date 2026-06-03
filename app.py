"""
Seralung Finance — Personal Financial Intelligence Tool
=======================================================
Architecture:
  - app.py              : Main entry point (this file). Handles routing between pages.
  - pages/auth.py       : Login / Create Account / Guest quick-check flow
  - pages/dashboard.py  : Full authenticated dashboard (Budget, Health, Portfolio, Plan)
  - utils/calculations.py : Pure financial calculation functions (no UI)
  - utils/charts.py     : Plotly chart builders (no UI side effects)
  - utils/styles.py     : All CSS / design tokens / UI helper components
  - utils/db.py         : In-memory user store (replace with SQLite or Postgres in production)

Run:
  streamlit run app.py

Dependencies:
  streamlit>=1.35.0
  plotly>=5.20.0
  numpy>=1.24.0
  pandas>=2.0.0
"""

import streamlit as st

# ─── Page config must be the FIRST streamlit call ─────────────────────────────
st.set_page_config(
    page_title="Seralung Finance",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── Internal imports (after set_page_config) ──────────────────────────────────
from pages.auth import render_auth_page
from pages.dashboard import render_dashboard


def detect_mobile() -> bool:
    """
    Server-side mobile detection via User-Agent header.
    Falls back to False (desktop) if the header is unavailable.
    """
    try:
        ua = st.context.headers.get("User-Agent", "") or ""
        mobile_keywords = ["Mobile", "Android", "iPhone", "iPad", "iPod", "Windows Phone"]
        return any(kw in ua for kw in mobile_keywords)
    except Exception:
        return False


def initialise_session_state() -> None:
    """
    Set all session-state defaults on first run.
    This is called once per browser session.
    """
    defaults = {
        # ── Authentication state ──────────────────────────────────────────
        "is_authenticated": False,      # True once user logs in or creates account
        "current_user": None,           # Username string
        "is_guest": False,              # True during the no-account quick check flow

        # ── Guest quick-check inputs ──────────────────────────────────────
        "guest_monthly_income": 0,
        "guest_rough_expenses": 0,
        "guest_total_savings": 0,
        "guest_quiz_complete": False,   # True after all 10 Q&A answered
        "guest_results_ready": False,   # True after results are calculated

        # ── Risk questionnaire answers (shared between guest and auth users) ──
        **{f"quiz_q{i}": 0 for i in range(1, 11)},

        # ── Authenticated user: budget data ───────────────────────────────
        "user_income_primary": None,
        "user_income_secondary": None,
        "user_savings": None,
        # List of dicts: [{id, name, category, amount}]
        "user_expenses": [],
        "next_expense_id": 1,

        # ── Navigation ────────────────────────────────────────────────────
        "active_tab": "budget",         # budget | health | portfolio | plan
        "is_mobile": detect_mobile(),
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def main() -> None:
    """
    Application entry point.
    Routes to auth page or dashboard depending on authentication state.
    """
    initialise_session_state()

    if st.session_state["is_authenticated"] or st.session_state["is_guest"]:
        render_dashboard()
    else:
        render_auth_page()


if __name__ == "__main__":
    main()

"""
pages/dashboard.py
==================
Authenticated dashboard for Seralung Finance.

Four tabs:
  1. Budget          — income inputs, expense management, 50/30/20 analysis
  2. Financial Health — health score gauge, risk questionnaire, risk analysis
  3. Investment Portfolio — model portfolio tiers with MPT metrics
  4. Action Plan     — prioritised action items and investment readiness

Users must be logged in (or continuing as guest with results) to reach this page.
"""

from __future__ import annotations

from typing import Dict, List, Tuple
import streamlit as st

from utils.styles import (
    inject_global_css,
    render_app_header,
    render_info_banner,
    render_section_header,
    render_metric_card,
    render_action_item,
    BG_PAGE, BG_CARD, BG_BORDER,
    TEXT_PRIMARY, TEXT_MUTED,
    COLOR_PRIMARY, COLOR_PRIMARY_BG, COLOR_PRIMARY_DK,
    COLOR_GREEN, COLOR_GREEN_BG,
    COLOR_AMBER, COLOR_AMBER_BG,
    COLOR_RED, COLOR_RED_BG,
    COLOR_TEAL, COLOR_TEAL_BG,
    COLOR_PURPLE, COLOR_PURPLE_BG,
    FONT_SANS, FONT_MONO,
)
from utils.calculations import (
    EXPENSE_CATEGORIES,
    RISK_QUESTIONS,
    PORTFOLIO_TIERS,
    PORTFOLIO_ASSETS,
    TIER_WEIGHTS,
    TIER_METRICS,
    TIER_INVESTMENT_OPTIONS,
    calculate_budget_summary,
    calculate_financial_health_score,
    get_health_rating,
    calculate_risk_capacity,
    calculate_quiz_score,
    get_risk_tolerance_profile,
    get_recommended_tier,
    generate_action_plan,
    calculate_investment_readiness,
)
from utils.charts import (
    build_circular_gauge,
    build_donut_chart,
    build_budget_comparison_bar,
    CATEGORY_COLOUR_PALETTE,
    PORTFOLIO_ASSET_COLOURS,
    TIER_COLOURS,
    TIER_BG_COLOURS,
)
from utils.user_store import save_user_financial_data


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def render_dashboard() -> None:
    """
    Render the full authenticated dashboard.
    Called from app.py when the user is authenticated or in guest-results mode.
    """
    is_mobile = st.session_state.get("is_mobile", False)

    inject_global_css(is_mobile)
    render_app_header(
        is_mobile,
        show_logout=st.session_state.get("is_authenticated", False),
    )

    # Display username greeting for authenticated users
    if st.session_state.get("is_authenticated"):
        username = st.session_state.get("current_user", "")
        if username:
            from utils.user_store import get_user_profile
            profile = get_user_profile(username)
            display_name = profile.get("display_name", username) if profile else username
            st.markdown(
                f"<div style='font-family:{FONT_SANS};font-size:0.85rem;"
                f"color:{TEXT_MUTED};padding:0 0 8px;'>"
                f"Welcome back, <strong style='color:{COLOR_PRIMARY};'>{display_name}</strong></div>",
                unsafe_allow_html=True,
            )

    # Render the four main tabs
    tab_budget, tab_health, tab_portfolio, tab_plan = st.tabs([
        "📊 Budget",
        "❤️ Financial Health",
        "💼 Investment Portfolio",
        "✅ Action Plan",
    ])

    with tab_budget:
        _render_budget_tab(is_mobile)

    with tab_health:
        _render_health_tab(is_mobile)

    with tab_portfolio:
        _render_portfolio_tab(is_mobile)

    with tab_plan:
        _render_action_plan_tab(is_mobile)

    # Render footer disclaimer
    _render_footer()


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: responsive columns
# ─────────────────────────────────────────────────────────────────────────────

def _responsive_columns(n: int, gap: str = "small") -> list:
    """
    Return n columns on desktop, or n stacked containers on mobile.
    This prevents horizontal overflow on 375px-wide phones.
    """
    if st.session_state.get("is_mobile", False):
        return [st.container() for _ in range(n)]
    return st.columns(n, gap=gap)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — BUDGET
# ─────────────────────────────────────────────────────────────────────────────

def _render_budget_tab(is_mobile: bool) -> None:
    """
    Budget tab: income inputs, expense manager, 50/30/20 analysis,
    category donut chart, and emergency fund runway.
    """
    render_info_banner(
        "Enter your income and add each expense by clicking <strong>+ Add expense</strong>. "
        "All budget metrics update instantly.",
        "info",
    )

    # ── Income & savings inputs ───────────────────────────────────────────
    render_section_header("INCOME & SAVINGS")

    inc_col1, inc_col2, inc_col3 = _responsive_columns(3, gap="medium")

    with inc_col1:
        st.markdown(f"<span style='font-family:{FONT_SANS};font-size:0.78rem;font-weight:600;color:{TEXT_MUTED};'>Monthly primary income ($)</span>", unsafe_allow_html=True)
        st.number_input(
            "Monthly primary income ($)",
            min_value=0.0,
            step=None,
            value=st.session_state.get("user_income_primary") or None,
            placeholder="e.g. 5000.00",
            key="user_income_primary",
            label_visibility="collapsed",
            format="%.2f",
        )
    with inc_col2:
        st.markdown(f"<span style='font-family:{FONT_SANS};font-size:0.78rem;font-weight:600;color:{TEXT_MUTED};'>Secondary income ($ optional)</span>", unsafe_allow_html=True)
        st.number_input(
            "Secondary income ($ optional)",
            min_value=0.0,
            step=None,
            value=st.session_state.get("user_income_secondary") or None,
            placeholder="e.g. 500.00",
            key="user_income_secondary",
            label_visibility="collapsed",
            format="%.2f",
        )
    with inc_col3:
        st.markdown(f"<span style='font-family:{FONT_SANS};font-size:0.78rem;font-weight:600;color:{TEXT_MUTED};'>Current cash savings ($)</span>", unsafe_allow_html=True)
        st.number_input(
            "Current cash savings ($)",
            min_value=0.0,
            step=None,
            value=st.session_state.get("user_savings") or None,
            placeholder="e.g. 10000.00",
            key="user_savings",
            label_visibility="collapsed",
            format="%.2f",
        )

    monthly_income = (
        (st.session_state.get("user_income_primary") or 0)
        + (st.session_state.get("user_income_secondary") or 0)
    )
    current_savings = st.session_state.get("user_savings") or 0

    # ── Expense manager ───────────────────────────────────────────────────
    render_section_header("YOUR EXPENSES")

    render_info_banner(
        "Click <strong>+ Add expense</strong> to add a new bill or expense line. "
        "You can edit the name, category, and amount for each entry.",
        "info",
    )

    # Show existing expenses
    expenses: List[Dict] = st.session_state.get("user_expenses", [])

    if expenses:
        _render_expense_list(expenses)
    else:
        st.markdown(
            f"<div style='background:{BG_CARD};border:1px solid {BG_BORDER};"
            f"border-radius:10px;padding:24px;text-align:center;margin:8px 0;'>"
            f"<div style='font-family:{FONT_SANS};font-size:1rem;color:{TEXT_MUTED};'>"
            f"No expenses added yet.</div>"
            f"<div style='font-family:{FONT_SANS};font-size:0.85rem;color:{TEXT_MUTED};"
            f"margin-top:4px;'>Click the button below to add your first expense.</div></div>",
            unsafe_allow_html=True,
        )

    # Add expense button
    if st.button("+ Add expense", key="btn_add_expense"):
        _add_expense()
        st.rerun()

    # ── Budget analysis ───────────────────────────────────────────────────
    if monthly_income <= 0:
        render_info_banner(
            "Enter your monthly income above to see your budget analysis.", "warn"
        )
        return

    # Compute all budget metrics
    budget = calculate_budget_summary(monthly_income, expenses, current_savings)
    st.session_state["_budget_cache"] = budget   # share with other tabs

    # Auto-save to user store when authenticated
    if st.session_state.get("is_authenticated"):
        _autosave_user_data(budget)

    render_section_header("BUDGET SUMMARY")

    sm1, sm2, sm3, sm4 = _responsive_columns(4, gap="small")

    with sm1:
        render_metric_card(
            "Total Income",
            f"${budget['income']:,.0f}",
            "Per month",
            TEXT_PRIMARY, BG_PAGE,
        )
    with sm2:
        expense_pct = budget["total_expenses"] / budget["income"] * 100
        render_metric_card(
            "Total Expenses",
            f"${budget['total_expenses']:,.0f}",
            f"{expense_pct:.0f}% of income",
            COLOR_AMBER, COLOR_AMBER_BG,
        )
    with sm3:
        surplus_colour = COLOR_GREEN if budget["monthly_surplus"] >= 0 else COLOR_RED
        surplus_bg     = COLOR_GREEN_BG if budget["monthly_surplus"] >= 0 else COLOR_RED_BG
        surplus_label  = (
            f"${budget['monthly_surplus']:,.0f}"
            if budget["monthly_surplus"] >= 0
            else f"-${abs(budget['monthly_surplus']):,.0f}"
        )
        render_metric_card(
            "Monthly Surplus",
            surplus_label,
            "Income − expenses",
            surplus_colour, surplus_bg,
        )
    with sm4:
        sr = budget["savings_rate"]
        sr_colour = (
            COLOR_GREEN if sr >= 0.20
            else COLOR_AMBER if sr >= 0.10
            else COLOR_RED
        )
        sr_bg = (
            COLOR_GREEN_BG if sr >= 0.20
            else COLOR_AMBER_BG if sr >= 0.10
            else COLOR_RED_BG
        )
        render_metric_card(
            "Savings Rate",
            f"{sr * 100:.1f}%",
            "Surplus ÷ income",
            sr_colour, sr_bg,
        )

    # ── 50/30/20 section ─────────────────────────────────────────────────
    render_section_header("50 / 30 / 20 RULE")

    income = budget["income"]
    needs_pct   = budget["needs"]   / income * 100
    wants_pct   = budget["wants"]   / income * 100
    savings_pct = max(0.0, budget["monthly_surplus"]) / income * 100

    bar_col, breakdown_col = _responsive_columns(2, gap="large")

    with bar_col:
        fig = build_budget_comparison_bar(needs_pct, wants_pct, savings_pct)
        st.plotly_chart(fig, use_container_width=True)

    with breakdown_col:
        st.markdown("<div style='padding-top:6px;'></div>", unsafe_allow_html=True)
        for label, actual, ideal, hint in [
            ("Needs",   needs_pct,   50, "housing, food, transport, insurance, debt"),
            ("Wants",   wants_pct,   30, "dining, entertainment, shopping, travel"),
            ("Savings", savings_pct, 20, "everything left over"),
        ]:
            on_track = (actual <= ideal + 2) if label != "Savings" else (actual >= ideal - 2)
            row_colour = COLOR_GREEN if on_track else COLOR_AMBER

            st.markdown(
                f"<div style='background:{BG_CARD};border:1px solid {BG_BORDER};"
                f"border-radius:8px;padding:9px 12px;margin-bottom:6px;'>"
                f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
                f"<span style='font-family:{FONT_SANS};font-weight:700;color:{TEXT_PRIMARY};"
                f"font-size:0.9rem;'>{label}</span>"
                f"<span style='font-family:{FONT_MONO};font-weight:700;color:{row_colour};"
                f"font-size:0.9rem;'>{actual:.0f}%"
                f"<span style='color:{TEXT_MUTED};font-weight:400;'> / {ideal}%</span></span></div>"
                f"<div style='font-family:{FONT_SANS};font-size:0.72rem;color:{TEXT_MUTED};"
                f"margin-top:2px;'>{hint}</div></div>",
                unsafe_allow_html=True,
            )

    # ── Category breakdown ────────────────────────────────────────────────
    render_section_header("WHERE YOUR MONEY GOES")

    cat_col, runway_col = _responsive_columns(2, gap="large")

    with cat_col:
        cat_totals = budget["category_totals"]
        if cat_totals:
            sorted_cats = dict(sorted(cat_totals.items(), key=lambda x: x[1], reverse=True))
            colours     = CATEGORY_COLOUR_PALETTE[:len(sorted_cats)]
            fig = build_donut_chart(
                labels=list(sorted_cats.keys()),
                values=list(sorted_cats.values()),
                colors=colours,
                center_label=f"${budget['total_expenses']:,.0f}",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            render_info_banner("Add expenses above to see the category breakdown.", "info")

    with runway_col:
        runway = budget["emergency_runway_months"]
        runway_colour = (
            COLOR_GREEN if runway >= 6
            else COLOR_AMBER if runway >= 3
            else COLOR_RED
        )
        runway_bg = (
            COLOR_GREEN_BG if runway >= 6
            else COLOR_AMBER_BG if runway >= 3
            else COLOR_RED_BG
        )
        render_metric_card(
            "Emergency Fund Runway",
            f"{runway:.1f} months",
            f"${current_savings:,.0f} savings ÷ ${budget['essential_monthly_spend']:,.0f}/mo essentials",
            runway_colour, runway_bg,
        )

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

        if runway < 3:
            render_info_banner(
                "Your emergency fund is below 3 months of essential expenses. "
                "This is the most important fix before investing.",
                "alert",
            )
        elif runway < 6:
            render_info_banner(
                "Aim for 6 months of essential expenses in accessible savings "
                "before taking on investment risk.",
                "warn",
            )
        else:
            render_info_banner(
                "Healthy emergency buffer — a solid foundation to invest from.",
                "good",
            )


def _render_expense_list(expenses: List[Dict]) -> None:
    """
    Render the list of expense rows with inline edit and delete controls.
    Each expense is an editable row: name, category dropdown, dollar amount, delete button.
    """
    # Header row
    st.markdown(
        f"<div style='display:grid;grid-template-columns:2fr 1.5fr 1fr 40px;"
        f"gap:8px;padding:6px 10px;'>"
        f"<span style='font-family:{FONT_SANS};font-size:0.72rem;color:{TEXT_MUTED};"
        f"font-weight:600;text-transform:uppercase;letter-spacing:0.04em;'>Expense</span>"
        f"<span style='font-family:{FONT_SANS};font-size:0.72rem;color:{TEXT_MUTED};"
        f"font-weight:600;text-transform:uppercase;letter-spacing:0.04em;'>Category</span>"
        f"<span style='font-family:{FONT_SANS};font-size:0.72rem;color:{TEXT_MUTED};"
        f"font-weight:600;text-transform:uppercase;letter-spacing:0.04em;'>Amount/mo</span>"
        f"<span></span></div>",
        unsafe_allow_html=True,
    )

    to_delete: List[int] = []

    for expense in expenses:
        exp_id  = expense["id"]
        col_name, col_cat, col_amt, col_del = st.columns([2, 1.5, 1, 0.3], gap="small")

        with col_name:
            expense["name"] = st.text_input(
                f"Name_{exp_id}",
                value=expense.get("name", ""),
                placeholder="e.g. Rent",
                label_visibility="collapsed",
                key=f"exp_name_{exp_id}",
            )
        with col_cat:
            current_cat = expense.get("category", "Other")
            cat_index = EXPENSE_CATEGORIES.index(current_cat) if current_cat in EXPENSE_CATEGORIES else 0
            expense["category"] = st.selectbox(
                f"Cat_{exp_id}",
                options=EXPENSE_CATEGORIES,
                index=cat_index,
                label_visibility="collapsed",
                key=f"exp_cat_{exp_id}",
            )
        with col_amt:
            raw_val = expense.get("amount")
            expense["amount"] = st.number_input(
                f"Amt_{exp_id}",
                min_value=0.0,
                step=None,
                value=float(raw_val) if raw_val else None,
                placeholder="0.00",
                label_visibility="collapsed",
                key=f"exp_amt_{exp_id}",
                format="%.2f",
            )
        with col_del:
            st.markdown("<div style='padding-top:4px;'></div>", unsafe_allow_html=True)
            if st.button("✕", key=f"del_exp_{exp_id}", help="Remove this expense"):
                to_delete.append(exp_id)

    # Apply deletions
    if to_delete:
        st.session_state["user_expenses"] = [
            e for e in st.session_state["user_expenses"]
            if e["id"] not in to_delete
        ]
        st.rerun()


def _add_expense() -> None:
    """Append a blank expense row to the user's expense list."""
    new_id = st.session_state.get("next_expense_id", 1)
    st.session_state["user_expenses"].append({
        "id":       new_id,
        "name":     "",
        "category": "Other",
        "amount":   0,
    })
    st.session_state["next_expense_id"] = new_id + 1


def _autosave_user_data(budget: Dict) -> None:
    """Persist the current session financial data to the in-memory user store."""
    username = st.session_state.get("current_user")
    if not username:
        return

    quiz_answers = [st.session_state.get(f"quiz_q{i}", 0) for i in range(1, 11)]

    save_user_financial_data(
        username         = username,
        income_primary   = st.session_state.get("user_income_primary",   0),
        income_secondary = st.session_state.get("user_income_secondary", 0),
        current_savings  = st.session_state.get("user_savings",          0),
        expenses         = st.session_state.get("user_expenses",         []),
        quiz_answers     = quiz_answers,
    )


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — FINANCIAL HEALTH
# ─────────────────────────────────────────────────────────────────────────────

def _render_health_tab(is_mobile: bool) -> None:
    """
    Financial health tab: composite health score gauge, score breakdown,
    10-question risk questionnaire, and risk analysis (tolerance vs capacity).
    """
    budget: Dict = st.session_state.get("_budget_cache", {})

    if not budget or budget.get("income", 0) <= 0:
        render_info_banner(
            "Complete the Budget tab first — financial health is calculated from "
            "your income and expenses.",
            "info",
        )
        return

    # ── Health score ──────────────────────────────────────────────────────
    health_score, score_breakdown = calculate_financial_health_score(budget)
    rating_label, rating_colour, rating_bg = get_health_rating(health_score)

    render_section_header("FINANCIAL HEALTH SCORE")

    gauge_col, breakdown_col = _responsive_columns(2, gap="large")

    with gauge_col:
        fig = build_circular_gauge(health_score, rating_colour)
        st.plotly_chart(fig, use_container_width=True)

        # Rating label below the gauge
        st.markdown(
            f"<div style='text-align:center;margin-top:-12px;'>"
            f"<span style='background:{rating_bg};color:{rating_colour};"
            f"font-family:{FONT_SANS};font-weight:700;font-size:0.95rem;"
            f"padding:4px 16px;border-radius:20px;'>{rating_label}</span></div>",
            unsafe_allow_html=True,
        )

    with breakdown_col:
        st.markdown("<div style='padding-top:4px;'></div>", unsafe_allow_html=True)
        for component_name, (earned, maximum) in score_breakdown.items():
            bar_pct = earned / maximum * 100
            bar_colour = (
                COLOR_GREEN if bar_pct >= 70
                else COLOR_AMBER if bar_pct >= 40
                else COLOR_RED
            )
            st.markdown(
                f"<div style='margin-bottom:7px;'>"
                f"<div style='display:flex;justify-content:space-between;"
                f"font-family:{FONT_SANS};font-size:0.82rem;margin-bottom:3px;'>"
                f"<span style='color:{TEXT_PRIMARY};font-weight:500;'>{component_name}</span>"
                f"<span style='color:{bar_colour};font-family:{FONT_MONO};font-weight:600;'>"
                f"{earned}/{maximum}</span></div>"
                f"<div style='height:6px;background:rgba(0,0,0,0.07);border-radius:3px;"
                f"overflow:hidden;'>"
                f"<div style='width:{bar_pct:.0f}%;height:100%;background:{bar_colour};"
                f"border-radius:3px;'></div></div></div>",
                unsafe_allow_html=True,
            )

    # Contextual health message
    cap_score, cap_level, cap_label = calculate_risk_capacity(budget)
    if health_score < 45:
        render_info_banner(
            "Your financial foundation needs work. Strengthening savings and your "
            "emergency fund will do more for your wealth right now than any investment decision.",
            "alert",
        )
    elif cap_level >= 4:
        render_info_banner(
            f"Strong financial position — your capacity to absorb investment volatility "
            f"is {cap_label.lower()}.",
            "good",
        )
    else:
        render_info_banner(
            f"Your financial health is {rating_label.lower()} and your risk capacity is "
            f"{cap_label.lower()}.",
            "info",
        )

    # ── Risk questionnaire ────────────────────────────────────────────────
    render_section_header("RISK PROFILE — 10 QUESTIONS", COLOR_TEAL)

    render_info_banner(
        "These questions measure your personal comfort with volatility "
        "(your risk tolerance). Your profile updates live as you answer.",
        "info",
    )

    for i, (question_text, options) in enumerate(RISK_QUESTIONS):
        question_key = f"quiz_q{i + 1}"

        with st.container(border=True):
            st.markdown(
                f"<div style='display:flex;gap:9px;align-items:flex-start;'>"
                f"<span style='background:{COLOR_TEAL_BG};color:{COLOR_TEAL};"
                f"font-family:{FONT_SANS};font-size:0.72rem;font-weight:700;"
                f"padding:2px 8px;border-radius:4px;flex-shrink:0;margin-top:2px;'>"
                f"{i + 1:02d}/10</span>"
                f"<span style='font-family:{FONT_SANS};font-size:0.95rem;font-weight:600;"
                f"color:{TEXT_PRIMARY};line-height:1.4;'>{question_text}</span></div>",
                unsafe_allow_html=True,
            )

            selected = st.radio(
                question_text,
                options=list(range(len(options))),
                format_func=lambda idx, opts=options: opts[idx],
                index=st.session_state.get(question_key, 0),
                key=f"health_radio_{question_key}",
                label_visibility="collapsed",
            )
            st.session_state[question_key] = selected

    # ── Risk analysis ─────────────────────────────────────────────────────
    answers         = [st.session_state.get(f"quiz_q{i}", 0) for i in range(1, 11)]
    quiz_score      = calculate_quiz_score(answers)
    profile_name, profile_level = get_risk_tolerance_profile(quiz_score)
    _, cap_level, cap_label     = calculate_risk_capacity(budget)
    recommended_tier, _         = get_recommended_tier(cap_level, profile_level)

    # Cache for other tabs
    st.session_state["_profile_name"]  = profile_name
    st.session_state["_profile_level"] = profile_level
    st.session_state["_cap_level"]     = cap_level
    st.session_state["_cap_label"]     = cap_label
    st.session_state["_health_score"]  = health_score

    profile_colour_map = {
        "Conservative":            (COLOR_TEAL,    COLOR_TEAL_BG),
        "Moderately Conservative": (COLOR_GREEN,   COLOR_GREEN_BG),
        "Balanced":                (COLOR_PRIMARY, COLOR_PRIMARY_BG),
        "Growth":                  (COLOR_AMBER,   COLOR_AMBER_BG),
        "Aggressive":              (COLOR_RED,     COLOR_RED_BG),
    }
    p_colour, p_bg = profile_colour_map.get(profile_name, (COLOR_PRIMARY, COLOR_PRIMARY_BG))
    cap_colour_map = [COLOR_RED, COLOR_RED, COLOR_AMBER, COLOR_TEAL, COLOR_GREEN]
    cap_bg_map     = [COLOR_RED_BG, COLOR_RED_BG, COLOR_AMBER_BG, COLOR_TEAL_BG, COLOR_GREEN_BG]
    c_colour = cap_colour_map[cap_level - 1]
    c_bg     = cap_bg_map[cap_level - 1]

    render_section_header("RISK ANALYSIS", COLOR_PURPLE)

    ra1, ra2, ra3 = _responsive_columns(3, gap="small")
    with ra1:
        render_metric_card(
            "Risk Tolerance",
            profile_name,
            f"Level {profile_level}/5 · score {quiz_score}/40",
            p_colour, p_bg,
        )
    with ra2:
        render_metric_card(
            "Risk Capacity",
            cap_label,
            f"Level {cap_level}/5 · from your budget",
            c_colour, c_bg,
        )
    with ra3:
        rec_colour = TIER_COLOURS.get(recommended_tier, COLOR_PRIMARY)
        rec_bg     = TIER_BG_COLOURS.get(recommended_tier, COLOR_PRIMARY_BG)
        render_metric_card(
            "Suggested Tier",
            recommended_tier,
            "Prudent match (lower of the two)",
            rec_colour, rec_bg,
        )

    # Gap analysis message
    gap = profile_level - cap_level
    if gap >= 2:
        render_info_banner(
            f"Your appetite for risk (<strong>{profile_name}</strong>) is well above what your "
            f"finances can currently support (<strong>{cap_label}</strong>). Starting below your "
            f"comfort level protects you from being forced to sell in a downturn.",
            "alert",
        )
    elif gap <= -2:
        render_info_banner(
            f"Your finances could support more risk (<strong>{cap_label}</strong>) than you are "
            f"comfortable with (<strong>{profile_name}</strong>). That is fine — comfort matters, "
            f"and you can step up gradually as confidence grows.",
            "info",
        )
    else:
        render_info_banner(
            "Your risk tolerance and financial capacity are well aligned — "
            "a strong position to build an investment plan from.",
            "good",
        )


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — INVESTMENT PORTFOLIO
# ─────────────────────────────────────────────────────────────────────────────

def _render_portfolio_tab(is_mobile: bool) -> None:
    """
    Investment portfolio tab: five model tiers, MPT metrics,
    recommended tier highlight, comparison table.
    """
    render_info_banner(
        "Five model portfolios from lowest to highest risk, with key risk "
        "and return metrics for each.",
        "info",
    )

    # Pull cached values from health tab (or use defaults)
    profile_level   = st.session_state.get("_profile_level", 3)
    cap_level       = st.session_state.get("_cap_level", 3)
    recommended_tier, rec_index = get_recommended_tier(cap_level, profile_level)

    if "_profile_level" not in st.session_state:
        render_info_banner(
            "Complete the Financial Health tab to see which tier is matched to you.",
            "warn",
        )
    else:
        rec_colour = TIER_COLOURS.get(recommended_tier, COLOR_PRIMARY)
        render_info_banner(
            f"Based on your risk capacity and tolerance, your suggested starting tier is "
            f"<strong style='color:{rec_colour};'>{recommended_tier}</strong>.",
            "good",
        )

    # Tier selector
    render_section_header("CHOOSE A TIER TO EXPLORE")

    selected_tier = st.selectbox(
        "Risk tier",
        options=PORTFOLIO_TIERS,
        index=rec_index - 1,
        label_visibility="collapsed",
        key="portfolio_tier_selector",
    )

    metrics = TIER_METRICS[selected_tier]
    t_colour = TIER_COLOURS.get(selected_tier, COLOR_PRIMARY)
    t_bg     = TIER_BG_COLOURS.get(selected_tier, COLOR_PRIMARY_BG)
    weights  = TIER_WEIGHTS[selected_tier]

    # Allocation donut + metrics side by side
    donut_col, stats_col = _responsive_columns(2, gap="large")

    with donut_col:
        # Only include assets with non-zero weights
        active_assets  = [(PORTFOLIO_ASSETS[i], weights[i]) for i in range(len(weights)) if weights[i] > 0]
        asset_labels   = [a for a, _ in active_assets]
        asset_values   = [v for _, v in active_assets]
        asset_colours  = [PORTFOLIO_ASSET_COLOURS.get(a, COLOR_PRIMARY) for a in asset_labels]

        fig = build_donut_chart(asset_labels, asset_values, asset_colours, selected_tier)
        st.plotly_chart(fig, use_container_width=True)

    with stats_col:
        # Tier header card
        is_recommended = (selected_tier == recommended_tier)
        suffix = " · suggested for you" if is_recommended else ""

        st.markdown(
            f"<div style='background:{t_bg};border:1px solid {BG_BORDER};"
            f"border-left:4px solid {t_colour};border-radius:0 12px 12px 0;"
            f"padding:14px 18px;margin-bottom:10px;'>"
            f"<div style='font-family:{FONT_SANS};font-size:1.5rem;font-weight:800;"
            f"color:{t_colour};'>{selected_tier}{suffix}</div>"
            f"<div style='font-family:{FONT_SANS};font-size:0.82rem;color:{TEXT_MUTED};"
            f"margin-top:2px;'>Expected return "
            f"<strong style='color:{TEXT_PRIMARY};'>{metrics['expected_return']*100:.1f}%</strong> p.a. · "
            f"Volatility <strong style='color:{TEXT_PRIMARY};'>{metrics['volatility']*100:.1f}%</strong>"
            f"</div></div>",
            unsafe_allow_html=True,
        )

        m1, m2 = _responsive_columns(2, gap="small")
        with m1:
            render_metric_card(
                "Sharpe Ratio",
                f"{metrics['sharpe_ratio']:.2f}",
                "Return per unit of risk",
                COLOR_PRIMARY, COLOR_PRIMARY_BG,
            )
            render_metric_card(
                "Value at Risk (95%)",
                f"{metrics['value_at_risk_95']*100:.1f}%",
                "Worst year in 20 (1-yr)",
                COLOR_RED, COLOR_RED_BG,
            )
        with m2:
            render_metric_card(
                "Diversification",
                f"{metrics['diversification_ratio']:.2f}×",
                "Higher = better spread",
                COLOR_TEAL, COLOR_TEAL_BG,
            )
            render_metric_card(
                "Est. Max Drawdown",
                f"{metrics['max_drawdown_estimate']*100:.0f}%",
                "Peak-to-trough estimate",
                COLOR_AMBER, COLOR_AMBER_BG,
            )

    # ── Investment options for this tier ──────────────────────────────────
    render_section_header(f"INVESTMENT OPTIONS — {selected_tier.upper()}", t_colour)

    for option in TIER_INVESTMENT_OPTIONS[selected_tier]:
        st.markdown(
            f"<div style='background:{BG_CARD};border:1px solid {BG_BORDER};"
            f"border-left:3px solid {t_colour};border-radius:0 8px 8px 0;"
            f"padding:8px 13px;margin-bottom:5px;font-family:{FONT_SANS};"
            f"font-size:0.88rem;color:{TEXT_PRIMARY};'>{option}</div>",
            unsafe_allow_html=True,
        )

    # ── All tiers comparison table ────────────────────────────────────────
    render_section_header("ALL TIERS COMPARED")

    header_cells = "".join(
        f"<th style='text-align:left;padding:7px 11px;background:{COLOR_PRIMARY};"
        f"color:#fff;font-family:{FONT_SANS};font-size:0.7rem;text-transform:uppercase;"
        f"letter-spacing:0.04em;font-weight:600;white-space:nowrap;'>{h}</th>"
        for h in ["Tier", "Exp. Return", "Volatility", "Sharpe", "VaR 95%", "CVaR 95%", "Max DD"]
    )

    row_cells = ""
    for i, tier in enumerate(PORTFOLIO_TIERS):
        m = TIER_METRICS[tier]
        is_rec  = (tier == recommended_tier)
        row_bg  = TIER_BG_COLOURS.get(tier, BG_CARD) if is_rec else (BG_CARD if i % 2 == 0 else BG_PAGE)
        star    = " ★" if is_rec else ""

        row_cells += (
            f"<tr style='background:{row_bg};'>"
            f"<td style='padding:8px 11px;font-family:{FONT_SANS};font-weight:700;"
            f"color:{TIER_COLOURS.get(tier, COLOR_PRIMARY)};border-bottom:1px solid {BG_BORDER};'>"
            f"{tier}{star}</td>"
            f"<td style='padding:8px 11px;font-family:{FONT_MONO};font-size:0.82rem;"
            f"color:{TEXT_PRIMARY};border-bottom:1px solid {BG_BORDER};'>"
            f"{m['expected_return']*100:.1f}%</td>"
            f"<td style='padding:8px 11px;font-family:{FONT_MONO};font-size:0.82rem;"
            f"color:{TEXT_PRIMARY};border-bottom:1px solid {BG_BORDER};'>"
            f"{m['volatility']*100:.1f}%</td>"
            f"<td style='padding:8px 11px;font-family:{FONT_MONO};font-size:0.82rem;"
            f"color:{TEXT_PRIMARY};border-bottom:1px solid {BG_BORDER};'>"
            f"{m['sharpe_ratio']:.2f}</td>"
            f"<td style='padding:8px 11px;font-family:{FONT_MONO};font-size:0.82rem;"
            f"color:{COLOR_RED};border-bottom:1px solid {BG_BORDER};'>"
            f"{m['value_at_risk_95']*100:.1f}%</td>"
            f"<td style='padding:8px 11px;font-family:{FONT_MONO};font-size:0.82rem;"
            f"color:{COLOR_RED};border-bottom:1px solid {BG_BORDER};'>"
            f"{m['conditional_var_95']*100:.1f}%</td>"
            f"<td style='padding:8px 11px;font-family:{FONT_MONO};font-size:0.82rem;"
            f"color:{COLOR_AMBER};border-bottom:1px solid {BG_BORDER};'>"
            f"{m['max_drawdown_estimate']*100:.0f}%</td>"
            f"</tr>"
        )

    st.markdown(
        f"<div style='border:1px solid {BG_BORDER};border-radius:10px;"
        f"overflow:hidden;overflow-x:auto;margin:4px 0;'>"
        f"<table style='width:100%;border-collapse:collapse;'>"
        f"<thead><tr>{header_cells}</tr></thead>"
        f"<tbody>{row_cells}</tbody></table></div>"
        f"<div style='font-family:{FONT_SANS};font-size:0.72rem;color:{TEXT_MUTED};"
        f"margin-top:6px;line-height:1.5;'>"
        f"<strong>VaR 95%</strong>: in the worst 1-in-20 year, losses are expected to exceed this. "
        f"<strong>CVaR 95%</strong>: the average loss in those worst-case years. "
        f"<strong>Max DD</strong>: estimated peak-to-trough fall. "
        f"Figures use long-run market assumptions, not forecasts.</div>",
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 — ACTION PLAN
# ─────────────────────────────────────────────────────────────────────────────

def _render_action_plan_tab(is_mobile: bool) -> None:
    """
    Action plan tab: investment readiness gauge, prioritised action items.
    """
    budget: Dict = st.session_state.get("_budget_cache", {})

    if not budget or budget.get("income", 0) <= 0:
        render_info_banner(
            "Complete the Budget and Financial Health tabs to generate your action plan.",
            "info",
        )
        return

    health_score  = st.session_state.get("_health_score", 0)
    profile_level = st.session_state.get("_profile_level", 3)
    profile_name  = st.session_state.get("_profile_name", "Balanced")
    cap_level     = st.session_state.get("_cap_level", 3)
    cap_label     = st.session_state.get("_cap_label", "Moderate")

    # If health tab hasn't been visited yet, compute now
    if not health_score:
        health_score, _ = calculate_financial_health_score(budget)

    action_plan  = generate_action_plan(
        budget         = budget,
        health_score   = health_score,
        capacity_level = cap_level,
        capacity_label = cap_label,
        tolerance_level= profile_level,
        tolerance_name = profile_name,
    )
    readiness_score = calculate_investment_readiness(health_score, action_plan)
    readiness_label, readiness_colour, readiness_bg = get_health_rating(readiness_score)

    recommended_tier, _ = get_recommended_tier(cap_level, profile_level)
    n_critical = sum(1 for k, _, _ in action_plan if k == "alert")
    n_warnings = sum(1 for k, _, _ in action_plan if k == "warn")

    # ── Readiness gauge ───────────────────────────────────────────────────
    render_section_header("INVESTMENT READINESS")

    gauge_col, summary_col = _responsive_columns(2, gap="large")

    with gauge_col:
        fig = build_circular_gauge(readiness_score, readiness_colour)
        st.plotly_chart(fig, use_container_width=True)

    with summary_col:
        rec_colour = TIER_COLOURS.get(recommended_tier, COLOR_PRIMARY)
        st.markdown(
            f"<div style='background:{readiness_bg};border:1px solid {BG_BORDER};"
            f"border-left:4px solid {readiness_colour};border-radius:0 12px 12px 0;"
            f"padding:16px 20px;margin-top:{'8px' if is_mobile else '30px'};'>"
            f"<div style='font-family:{FONT_SANS};font-size:0.72rem;color:{TEXT_MUTED};"
            f"font-weight:600;text-transform:uppercase;letter-spacing:0.04em;'>Overall</div>"
            f"<div style='font-family:{FONT_SANS};font-size:1.5rem;font-weight:800;"
            f"color:{readiness_colour};'>{readiness_label}</div>"
            f"<div style='font-family:{FONT_SANS};font-size:0.85rem;color:{TEXT_MUTED};"
            f"margin-top:4px;line-height:1.5;'>"
            f"{n_critical} critical item{'s' if n_critical != 1 else ''} and "
            f"{n_warnings} to watch. Suggested portfolio: "
            f"<strong style='color:{rec_colour};'>{recommended_tier}</strong>.</div></div>",
            unsafe_allow_html=True,
        )

    # ── Prioritised action items ──────────────────────────────────────────
    render_section_header("YOUR PRIORITISED ACTIONS", COLOR_PURPLE)

    for rank, (kind, title, description) in enumerate(action_plan, start=1):
        render_action_item(rank, title, description, kind)


# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────

def _render_footer() -> None:
    """Render the page-level footer disclaimer."""
    st.markdown(
        f"<div style='border-top:1px solid {BG_BORDER};margin-top:2rem;"
        f"padding:14px 0 6px;font-family:{FONT_SANS};font-size:0.74rem;"
        f"color:{TEXT_MUTED};text-align:center;'>"
        f"<strong style='color:{COLOR_PRIMARY};'>Seralung Finance</strong>"
        f" &nbsp;·&nbsp; Understand Risk. Invest with Confidence."
        f"<br><span style='font-size:0.68rem;'>Educational purposes only — "
        f"not personal financial advice — consult a licensed financial adviser "
        f"before investing.</span></div>",
        unsafe_allow_html=True,
    )

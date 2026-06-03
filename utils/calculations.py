"""
utils/calculations.py
=====================
Pure financial calculation functions.

All functions here are stateless — they take plain Python data as
arguments and return plain Python data.  No Streamlit calls, no session
state reads/writes.  This makes them easy to unit-test and reuse.
"""

from __future__ import annotations

import math
import numpy as np
from typing import Dict, List, Tuple


# ─────────────────────────────────────────────────────────────────────────────
# EXPENSE CATEGORY TAXONOMY
# ─────────────────────────────────────────────────────────────────────────────

#: All valid expense categories users can assign to a bill
EXPENSE_CATEGORIES: List[str] = [
    "Housing", "Utilities", "Groceries", "Transport", "Insurance",
    "Healthcare", "Debt Repayment", "Dining Out", "Entertainment",
    "Shopping", "Subscriptions", "Travel", "Savings/Invest", "Other",
]

#: Maps each category to its 50/30/20 bucket
CATEGORY_BUCKET: Dict[str, str] = {
    "Housing":        "need",
    "Utilities":      "need",
    "Groceries":      "need",
    "Transport":      "need",
    "Insurance":      "need",
    "Healthcare":     "need",
    "Debt Repayment": "need",
    "Dining Out":     "want",
    "Entertainment":  "want",
    "Shopping":       "want",
    "Subscriptions":  "want",
    "Travel":         "want",
    "Savings/Invest": "savings",
    "Other":          "want",
}


# ─────────────────────────────────────────────────────────────────────────────
# BUDGET CALCULATIONS
# ─────────────────────────────────────────────────────────────────────────────

def calculate_budget_summary(
    monthly_income: float,
    expenses: List[Dict],
    current_savings: float,
) -> Dict:
    """
    Compute all budget-derived metrics from raw inputs.

    Parameters
    ----------
    monthly_income  : combined primary + secondary income
    expenses        : list of {name, category, amount} dicts
    current_savings : total liquid savings (emergency fund)

    Returns
    -------
    Dict with keys:
        income, total_expenses, needs, wants, savings_bucket,
        debt_repayments, monthly_surplus, savings_rate,
        emergency_runway_months, essential_monthly_spend,
        debt_to_income_ratio, category_totals
    """
    total_expenses      = 0.0
    needs               = 0.0
    wants               = 0.0
    savings_bucket      = 0.0
    debt_repayments     = 0.0
    category_totals: Dict[str, float] = {}

    for expense in expenses:
        amount = max(0.0, float(expense.get("amount", 0) or 0))
        if amount <= 0:
            continue

        category = expense.get("category", "Other")
        bucket   = CATEGORY_BUCKET.get(category, "want")

        total_expenses += amount
        category_totals[category] = category_totals.get(category, 0.0) + amount

        if bucket == "need":
            needs += amount
        elif bucket == "savings":
            savings_bucket += amount
        else:
            wants += amount

        if category == "Debt Repayment":
            debt_repayments += amount

    # Monthly surplus is income minus ALL expenses (including savings bucket line items)
    monthly_surplus = monthly_income - total_expenses

    # Savings rate = surplus as fraction of income (can be negative)
    savings_rate = monthly_surplus / monthly_income if monthly_income > 0 else 0.0

    # Essential spend = needs only (used for emergency fund runway)
    essential_monthly = needs if needs > 0 else total_expenses

    # Emergency runway in months
    emergency_runway = (
        current_savings / essential_monthly if essential_monthly > 0 else 0.0
    )

    # Debt-to-income ratio
    debt_to_income = debt_repayments / monthly_income if monthly_income > 0 else 0.0

    return {
        "income":                  monthly_income,
        "total_expenses":          total_expenses,
        "needs":                   needs,
        "wants":                   wants,
        "savings_bucket":          savings_bucket,
        "debt_repayments":         debt_repayments,
        "monthly_surplus":         monthly_surplus,
        "savings_rate":            savings_rate,
        "emergency_runway_months": emergency_runway,
        "essential_monthly_spend": essential_monthly,
        "debt_to_income_ratio":    debt_to_income,
        "current_savings":         current_savings,
        "category_totals":         category_totals,
    }


def calculate_guest_budget_summary(
    monthly_income: float,
    rough_expenses: float,
    current_savings: float,
) -> Dict:
    """
    Simplified budget summary for the guest quick-check flow.
    No expense breakdown is available — uses a single estimated total.
    """
    monthly_surplus = monthly_income - rough_expenses
    savings_rate    = monthly_surplus / monthly_income if monthly_income > 0 else 0.0
    emergency_runway = (
        current_savings / rough_expenses if rough_expenses > 0 else 0.0
    )
    debt_to_income = 0.0  # unknown in guest flow

    return {
        "income":                  monthly_income,
        "total_expenses":          rough_expenses,
        "needs":                   rough_expenses,        # treat all as needs (conservative)
        "wants":                   0.0,
        "savings_bucket":          0.0,
        "debt_repayments":         0.0,
        "monthly_surplus":         monthly_surplus,
        "savings_rate":            savings_rate,
        "emergency_runway_months": emergency_runway,
        "essential_monthly_spend": rough_expenses,
        "debt_to_income_ratio":    debt_to_income,
        "current_savings":         current_savings,
        "category_totals":         {},
    }


# ─────────────────────────────────────────────────────────────────────────────
# FINANCIAL HEALTH SCORE
# ─────────────────────────────────────────────────────────────────────────────

def calculate_financial_health_score(budget: Dict) -> Tuple[int, Dict]:
    """
    Calculate a composite financial health score (0–100).

    Scoring components:
        Savings rate       30 pts   (20% or more = full marks)
        Emergency runway   25 pts   (6 months or more = full marks)
        Needs control      20 pts   (≤50% of income = full marks)
        Wants control      15 pts   (≤30% of income = full marks)
        Debt load          10 pts   (≤20% of income = full marks)

    Returns
    -------
    (total_score, breakdown_dict)
    breakdown_dict maps component name → (earned_points, max_points)
    """
    income = budget["income"]
    if income <= 0:
        return 0, {}

    savings_rate   = budget["savings_rate"]
    runway_months  = budget["emergency_runway_months"]
    needs_ratio    = budget["needs"] / income
    wants_ratio    = budget["wants"] / income
    dti            = budget["debt_to_income_ratio"]

    # Each component scored on a linear scale up to its maximum
    score_savings  = 30 if savings_rate >= 0.20 else max(0.0, savings_rate) / 0.20 * 30
    score_runway   = min(25.0, runway_months / 6 * 25)
    score_needs    = 20 if needs_ratio <= 0.50 else max(0.0, 20 - (needs_ratio - 0.50) * 80)
    score_wants    = 15 if wants_ratio <= 0.30 else max(0.0, 15 - (wants_ratio - 0.30) * 60)
    score_debt     = 10 if dti <= 0.20         else max(0.0, 10 - (dti - 0.20) * 40)

    total = round(min(100.0, score_savings + score_runway + score_needs + score_wants + score_debt))

    breakdown = {
        "Savings rate":     (round(score_savings), 30),
        "Emergency runway": (round(score_runway),  25),
        "Needs control":    (round(score_needs),   20),
        "Wants control":    (round(score_wants),   15),
        "Debt load":        (round(score_debt),    10),
    }

    return total, breakdown


def get_health_rating(score: int) -> Tuple[str, str, str]:
    """
    Convert a numeric health score to a label, colour, and background colour.

    Returns
    -------
    (label, hex_colour, hex_bg_colour)
    """
    from utils.styles import (
        COLOR_GREEN, COLOR_GREEN_BG, COLOR_TEAL, COLOR_TEAL_BG,
        COLOR_AMBER, COLOR_AMBER_BG, COLOR_RED, COLOR_RED_BG,
    )
    if score >= 80:
        return "Excellent", COLOR_GREEN, COLOR_GREEN_BG
    if score >= 65:
        return "Good",      COLOR_TEAL,  COLOR_TEAL_BG
    if score >= 45:
        return "Fair",      COLOR_AMBER, COLOR_AMBER_BG
    if score >= 25:
        return "At Risk",   COLOR_RED,   COLOR_RED_BG
    return "Critical",      COLOR_RED,   COLOR_RED_BG


# ─────────────────────────────────────────────────────────────────────────────
# RISK QUESTIONNAIRE
# ─────────────────────────────────────────────────────────────────────────────

#: 10 risk-tolerance questions — (question_text, [options])
RISK_QUESTIONS: List[Tuple[str, List[str]]] = [
    (
        "When do you expect to need this money?",
        ["Under 3 years", "3–7 years", "7–15 years", "15+ years"],
    ),
    (
        "How stable is your income?",
        ["Retired or fixed income", "Variable or self-employed", "Stable salary", "Very secure"],
    ),
    (
        "If your portfolio fell 30% in three months, you would:",
        ["Sell everything", "Sell some", "Hold and wait", "Buy more at lower prices"],
    ),
    (
        "How much investing experience do you have?",
        ["None", "Basic — shares & funds", "Three or more years active", "Ten or more years, multi-asset"],
    ),
    (
        "Your primary investment goal:",
        ["Protect capital", "Modest growth with protection", "Balanced growth", "Maximum growth"],
    ),
    (
        "Do you expect significant withdrawals within five years?",
        ["Yes — most of it", "Yes — a meaningful portion", "Possibly — small amounts", "No — long-term"],
    ),
    (
        "Maximum annual loss you could absorb:",
        ["Under 5%", "5–15%", "15–25%", "25% or more"],
    ),
    (
        "This investment is what share of your net worth?",
        ["Over 75%", "50–75%", "25–50%", "Under 25%"],
    ),
    (
        "How do market swings make you feel?",
        ["Very anxious", "Uneasy", "Mostly calm", "Indifferent — it is normal"],
    ),
    (
        "Your investment knowledge level:",
        ["Beginner", "Some understanding", "Confident", "Advanced"],
    ),
]


def calculate_quiz_score(answers: List[int]) -> int:
    """
    Convert a list of 10 zero-indexed answers into a total risk score.
    Each answer adds (index + 1) to the total, giving a range of 10–40.
    """
    return sum(ans + 1 for ans in answers)


def get_risk_tolerance_profile(quiz_score: int) -> Tuple[str, int]:
    """
    Map a raw quiz score (10–40) to a named risk tolerance profile.

    Returns
    -------
    (profile_name, level_1_to_5)
    """
    if quiz_score <= 18:
        return "Conservative",            1
    if quiz_score <= 25:
        return "Moderately Conservative", 2
    if quiz_score <= 31:
        return "Balanced",                3
    if quiz_score <= 36:
        return "Growth",                  4
    return "Aggressive",                  5


# ─────────────────────────────────────────────────────────────────────────────
# RISK CAPACITY  (budget-derived)
# ─────────────────────────────────────────────────────────────────────────────

def calculate_risk_capacity(budget: Dict) -> Tuple[int, int, str]:
    """
    Derive how much investment risk the user's finances can absorb.
    Unlike risk tolerance (psychological), this is purely numerical.

    Components:
        Emergency runway contribution  40%
        Savings rate contribution      40%
        Debt-to-income contribution    20%

    Returns
    -------
    (capacity_score_0_100, capacity_level_1_5, capacity_label)
    """
    runway_score = min(100.0, budget["emergency_runway_months"] / 6 * 100)
    sr_score     = min(100.0, max(0.0, budget["savings_rate"]) / 0.25 * 100)
    dti_score    = max(0.0,  100.0 - budget["debt_to_income_ratio"] / 0.50 * 100)

    score = round(0.40 * runway_score + 0.40 * sr_score + 0.20 * dti_score)

    if score >= 80:
        return score, 5, "Strong"
    if score >= 60:
        return score, 4, "Solid"
    if score >= 40:
        return score, 3, "Moderate"
    if score >= 20:
        return score, 2, "Limited"
    return score, 1, "Fragile"


# ─────────────────────────────────────────────────────────────────────────────
# INVESTMENT PORTFOLIO ENGINE  (Modern Portfolio Theory)
# ─────────────────────────────────────────────────────────────────────────────

#: Asset class names used throughout the portfolio engine
PORTFOLIO_ASSETS = ["Cash", "Bonds", "Equity ETFs", "Stocks", "Property", "Crypto"]

#: Long-run expected annual returns per asset class
EXPECTED_RETURNS = np.array([0.035, 0.045, 0.080, 0.095, 0.070, 0.180])

#: Annual volatility (standard deviation) per asset class
ASSET_VOLATILITIES = np.array([0.010, 0.050, 0.150, 0.240, 0.140, 0.650])

#: Risk-free rate (approximating RBA cash rate)
RISK_FREE_RATE = 0.035

#: Correlation matrix between asset classes (6×6)
CORRELATION_MATRIX = np.array([
    [ 1.00,  0.15,  0.00, -0.05,  0.05,  0.00],
    [ 0.15,  1.00,  0.25,  0.10,  0.30,  0.05],
    [ 0.00,  0.25,  1.00,  0.88,  0.60,  0.35],
    [-0.05,  0.10,  0.88,  1.00,  0.50,  0.40],
    [ 0.05,  0.30,  0.60,  0.50,  1.00,  0.25],
    [ 0.00,  0.05,  0.35,  0.40,  0.25,  1.00],
])

#: Covariance matrix derived from volatilities and correlations
COVARIANCE_MATRIX = np.outer(ASSET_VOLATILITIES, ASSET_VOLATILITIES) * CORRELATION_MATRIX

#: Model portfolio tiers (ordered lowest → highest risk)
PORTFOLIO_TIERS = ["Defensive", "Conservative", "Balanced", "Growth", "Aggressive"]

#: Target asset weights (%) for each tier: [Cash, Bonds, EquityETFs, Stocks, Property, Crypto]
TIER_WEIGHTS: Dict[str, List[int]] = {
    "Defensive":    [40, 40, 12,  0,  8,  0],
    "Conservative": [22, 33, 25,  3, 15,  2],
    "Balanced":     [10, 22, 35, 10, 18,  5],
    "Growth":       [ 5, 12, 45, 18, 15,  5],
    "Aggressive":   [ 2,  5, 48, 25, 12,  8],
}

#: Specific investment vehicles recommended for each tier
TIER_INVESTMENT_OPTIONS: Dict[str, List[str]] = {
    "Defensive": [
        "High-interest savings accounts & term deposits",
        "Government bond ETFs (e.g. VGB, IAF)",
        "Cash management / money-market funds",
        "Capital-guaranteed products",
    ],
    "Conservative": [
        "Diversified bond ETFs (corporate + government)",
        "Blue-chip dividend ETFs",
        "Small allocation to broad index funds",
        "Defensive listed property (A-REIT ETFs)",
    ],
    "Balanced": [
        "Broad-market index ETFs (VAS, VGS, IVV)",
        "Balanced multi-asset funds (~60/40)",
        "Listed property / infrastructure ETFs",
        "Investment-grade bond ETFs for ballast",
    ],
    "Growth": [
        "Global & domestic equity ETFs (growth tilt)",
        "International index funds (developed + emerging)",
        "Sector / thematic ETFs as satellites",
        "Small allocation to quality individual stocks",
    ],
    "Aggressive": [
        "Growth & thematic equity ETFs",
        "Emerging-market & small-cap ETFs",
        "Selective individual growth stocks",
        "Small, capped crypto allocation (under 10%)",
    ],
}


def calculate_portfolio_metrics(weights_percent: List[int]) -> Dict:
    """
    Calculate MPT-based risk and return metrics for a given asset allocation.

    Parameters
    ----------
    weights_percent : list of 6 integers summing to ~100 (percentage weights)

    Returns
    -------
    Dict with keys:
        expected_return, volatility, sharpe_ratio,
        value_at_risk_95, conditional_var_95,
        diversification_ratio, max_drawdown_estimate
    """
    weights = np.array(weights_percent, dtype=float) / 100.0

    # Expected portfolio return (weighted average)
    portfolio_return = float(weights @ EXPECTED_RETURNS)

    # Portfolio standard deviation (σ = √(w'Σw))
    portfolio_vol = float(weights @ COVARIANCE_MATRIX @ weights) ** 0.5

    # Sharpe ratio: excess return per unit of risk
    sharpe = (portfolio_return - RISK_FREE_RATE) / portfolio_vol if portfolio_vol > 0 else 0.0

    # Value at Risk at 95% confidence (1-year horizon)
    z_score = 1.645
    var_95 = max(0.0, z_score * portfolio_vol - portfolio_return)

    # Conditional VaR (Expected Shortfall) — average loss in the worst 5% of years
    phi_05 = 0.103138  # standard normal PDF at 1.645
    cvar_95 = max(0.0, portfolio_vol * (phi_05 / 0.05) - portfolio_return)

    # Diversification ratio: weighted avg individual vols / portfolio vol
    weighted_individual_vol = float(weights @ ASSET_VOLATILITIES)
    diversification_ratio = weighted_individual_vol / portfolio_vol if portfolio_vol > 0 else 1.0

    # Estimated maximum drawdown (empirical approximation)
    max_drawdown = min(0.95, 2.4 * portfolio_vol)

    return {
        "expected_return":       portfolio_return,
        "volatility":            portfolio_vol,
        "sharpe_ratio":          sharpe,
        "value_at_risk_95":      var_95,
        "conditional_var_95":    cvar_95,
        "diversification_ratio": diversification_ratio,
        "max_drawdown_estimate": max_drawdown,
    }


# Pre-compute metrics for all tiers at import time
TIER_METRICS: Dict[str, Dict] = {
    tier: calculate_portfolio_metrics(TIER_WEIGHTS[tier])
    for tier in PORTFOLIO_TIERS
}


def get_recommended_tier(capacity_level: int, tolerance_level: int) -> Tuple[str, int]:
    """
    Recommend the most appropriate portfolio tier.
    Uses the *lower* of capacity and tolerance to err on the side of caution.

    Returns
    -------
    (tier_name, tier_index_1_to_5)
    """
    index = max(1, min(5, min(capacity_level, tolerance_level)))
    return PORTFOLIO_TIERS[index - 1], index


# ─────────────────────────────────────────────────────────────────────────────
# ACTION PLAN GENERATOR
# ─────────────────────────────────────────────────────────────────────────────

def generate_action_plan(
    budget: Dict,
    health_score: int,
    capacity_level: int,
    capacity_label: str,
    tolerance_level: int,
    tolerance_name: str,
) -> List[Tuple[str, str, str]]:
    """
    Generate a prioritised list of financial action items.

    Returns
    -------
    List of (kind, title, description) tuples, sorted by urgency.
    kind is one of "alert" | "warn" | "info" | "good".
    """
    actions: List[Tuple[str, str, str]] = []
    recommended_tier, _ = get_recommended_tier(capacity_level, tolerance_level)

    # ── Emergency fund checks ─────────────────────────────────────────────
    runway = budget["emergency_runway_months"]
    surplus = budget["monthly_surplus"]

    if runway < 3:
        target_fund = budget["essential_monthly_spend"] * 6
        shortfall   = max(0.0, target_fund - budget["current_savings"])
        months_to_goal = shortfall / surplus if surplus > 0 else math.inf

        if surplus > 0:
            description = (
                f"You have {runway:.1f} months of essential expenses saved. Aim for 6 months "
                f"(~${target_fund:,.0f}). At your current surplus of ${surplus:,.0f}/mo, "
                f"that is about {months_to_goal:.0f} months away."
            )
        else:
            description = (
                f"You have {runway:.1f} months saved and no monthly surplus — freeing up "
                f"cash flow is the priority before building the buffer."
            )
        actions.append(("alert", "Build your emergency fund first", description))

    elif runway < 6:
        actions.append((
            "warn",
            "Top up your emergency fund",
            f"You have {runway:.1f} months saved. Building to 6 months gives a full "
            f"buffer before taking investment risk.",
        ))

    # ── Spending checks ───────────────────────────────────────────────────
    sr = budget["savings_rate"]
    income = budget["income"]

    if sr < 0:
        actions.append((
            "alert",
            "You are spending more than you earn",
            f"Your expenses exceed income by ${abs(surplus):,.0f}/mo. Reducing your "
            f"largest discretionary categories is the immediate priority — no investment "
            f"can outrun a monthly deficit.",
        ))
    elif sr < 0.10:
        actions.append((
            "warn",
            "Lift your savings rate",
            f"You are saving {sr*100:.0f}% of income. Reaching 20% "
            f"(${income * 0.20:,.0f}/mo) accelerates every financial goal. "
            f"Trimming 'wants' is usually the fastest lever.",
        ))

    needs_ratio = budget["needs"] / income if income > 0 else 0
    wants_ratio = budget["wants"] / income if income > 0 else 0

    if needs_ratio > 0.55:
        actions.append((
            "warn",
            "Fixed costs are high",
            f"Needs are {needs_ratio*100:.0f}% of income (ideal ≤50%). Housing, transport, "
            f"and insurance are the usual culprits — structural changes here free up the most room.",
        ))

    if wants_ratio > 0.32:
        actions.append((
            "info",
            "Discretionary spending is above the guide",
            f"Wants are {wants_ratio*100:.0f}% of income (ideal ≤30%). Redirecting part "
            f"of this to savings compounds meaningfully over time.",
        ))

    # ── Debt check ────────────────────────────────────────────────────────
    dti = budget["debt_to_income_ratio"]
    if dti > 0.20:
        actions.append((
            "warn",
            "Debt load is elevated",
            f"Debt repayments are {dti*100:.0f}% of income. Clearing high-interest debt "
            f"is effectively a guaranteed return and usually beats investing while rates are high.",
        ))

    # ── Risk alignment check ──────────────────────────────────────────────
    gap = tolerance_level - capacity_level
    if gap >= 2:
        actions.append((
            "alert",
            "Do not invest beyond your capacity",
            f"Your comfort with risk ({tolerance_name}) is well above what your finances "
            f"support ({capacity_label}). Start at the {recommended_tier} tier and step up "
            f"only as your buffer and surplus grow.",
        ))
    elif gap <= -2:
        actions.append((
            "info",
            "You can afford more growth when ready",
            f"Your finances ({capacity_label}) could support more risk than your current "
            f"comfort ({tolerance_name}). There is no rush — increase exposure gradually "
            f"as confidence builds.",
        ))

    # ── Positive signal ───────────────────────────────────────────────────
    if health_score >= 65 and runway >= 6:
        actions.append((
            "good",
            "You are ready to invest systematically",
            f"Strong foundation. Consider directing your ${max(0.0, surplus):,.0f}/mo surplus "
            f"into the {recommended_tier} portfolio via regular, automated contributions "
            f"to smooth out market timing.",
        ))

    # If no warnings at all, add a general positive note
    has_warnings = any(k in ("alert", "warn") for k, _, _ in actions)
    if not has_warnings:
        actions.append((
            "good",
            "Your finances are in good shape",
            "No critical issues detected. Keep contributing consistently and review "
            "quarterly as your situation changes.",
        ))

    # Sort: alert → warn → info → good
    priority_order = {"alert": 0, "warn": 1, "info": 2, "good": 3}
    actions.sort(key=lambda item: priority_order.get(item[0], 4))

    return actions


def calculate_investment_readiness(
    health_score: int,
    action_plan: List[Tuple[str, str, str]],
) -> int:
    """
    Derive an investment readiness score from the health score and action plan.
    Penalises for critical items and warnings.

    Returns
    -------
    score between 0 and 100
    """
    n_critical = sum(1 for kind, _, _ in action_plan if kind == "alert")
    n_warnings = sum(1 for kind, _, _ in action_plan if kind == "warn")
    readiness  = max(0, min(100, health_score - n_critical * 12 - n_warnings * 5))
    return readiness

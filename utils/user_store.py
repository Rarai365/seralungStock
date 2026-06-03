"""
utils/user_store.py
===================
In-memory user store for the Seralung Finance app.

In production, replace this module with a proper database (SQLite,
PostgreSQL via psycopg2, or a cloud DB).  The function signatures here
serve as the interface contract — callers should not need to change.

Security note: Passwords are stored as plain strings here for
demonstration only.  In production use bcrypt or argon2 hashing.
"""

from __future__ import annotations

from typing import Optional, Dict, Any


# ─────────────────────────────────────────────────────────────────────────────
# IN-MEMORY STORE
# ─────────────────────────────────────────────────────────────────────────────

# Structure: { username: { "password": str, "profile": dict } }
_USER_STORE: Dict[str, Dict[str, Any]] = {}


def user_exists(username: str) -> bool:
    """Return True if a user with that username is registered."""
    return username.lower() in _USER_STORE


def create_user(username: str, password: str) -> bool:
    """
    Register a new user with an empty profile.

    Returns
    -------
    True on success, False if the username is already taken.
    """
    key = username.lower().strip()
    if not key or key in _USER_STORE:
        return False

    _USER_STORE[key] = {
        "password": password,
        "display_name": username.strip(),
        # Financial data — starts empty; user fills in after account creation
        "income_primary":   0,
        "income_secondary": 0,
        "current_savings":  0,
        "expenses":         [],   # list of {id, name, category, amount}
        "next_expense_id":  1,
        # Risk quiz answers (0-indexed)
        "quiz_answers":     [0] * 10,
    }
    return True


def verify_login(username: str, password: str) -> bool:
    """
    Verify username + password.

    Returns
    -------
    True if credentials are correct, False otherwise.
    """
    key = username.lower().strip()
    user = _USER_STORE.get(key)
    if user is None:
        return False
    return user["password"] == password


def get_user_profile(username: str) -> Optional[Dict]:
    """
    Return the full user profile dict, or None if not found.
    The caller receives a reference — mutations affect the store.
    For production, return a copy.
    """
    return _USER_STORE.get(username.lower().strip())


def save_user_financial_data(
    username: str,
    income_primary: float,
    income_secondary: float,
    current_savings: float,
    expenses: list,
    quiz_answers: list,
) -> None:
    """
    Persist the user's financial inputs back to the store.
    Call this whenever the user updates their data.
    """
    key = username.lower().strip()
    if key not in _USER_STORE:
        return

    _USER_STORE[key].update({
        "income_primary":   income_primary,
        "income_secondary": income_secondary,
        "current_savings":  current_savings,
        "expenses":         expenses,
        "quiz_answers":     quiz_answers,
    })

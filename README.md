# Seralung Finance

**Understand Risk. Invest with Confidence.**

A personal financial intelligence tool built with Python and Streamlit. Helps Australians connect their day-to-day budget to a risk-appropriate investment recommendation — in one place, with no manual calculation needed.

---

## What This App Does

Most financial tools either track your budget *or* guide your investments — never both. Seralung Finance bridges that gap: enter your income and expenses → get your financial health score → receive a matched investment recommendation — in one flow.

---

## Pages & Routes

The app simulates distinct pages via session state routing, similar to a multi-page web app.

| Route | Description |
|-------|-------------|
| `/home` | Full-screen split layout — hero panel left, sign-in form right (Facebook-style) |
| `/login` | Dedicated sign-in page — centred card, clean form |
| `/signup` | Dedicated create-account page — validation, auto-login on success |
| `/guest` | 3-step quick health check — no account needed |
| `/dashboard` | Full authenticated dashboard — 4 tabs (Budget, Health, Portfolio, Plan) |

---

## Features

### No-Account Quick Check (`/guest`)
Three steps — no sign-up required:
1. Enter monthly income, rough total expenses, and total savings
2. Answer 10 risk-tolerance questions (live profile preview updates as you go)
3. See your financial health score and risk profile — then unlock full detail by creating an account

### Authenticated Dashboard — Four Tabs

| Tab | What it does |
|-----|-------------|
| **Budget** | Add individual expenses by name and category. See 50/30/20 split, emergency fund runway, monthly surplus, and category donut chart |
| **Financial Health** | Composite health score (0–100) with breakdown bars. 10-question risk questionnaire. Risk tolerance vs financial capacity analysis |
| **Investment Portfolio** | 5 model tiers (Defensive → Aggressive) with MPT metrics: Sharpe ratio, VaR 95%, CVaR, max drawdown, diversification ratio. Per-tier investment vehicle suggestions |
| **Action Plan** | Investment readiness gauge. Prioritised action items tagged: Do first / Important / Consider / On track |

---

## Project Structure

```
seralung-finance/
├── app.py                    # Entry point — initialises session state, routes to auth or dashboard
├── pages/
│   ├── __init__.py
│   ├── auth.py               # Login / Register / Guest 3-step flow (separate full-screen pages)
│   └── dashboard.py          # Full authenticated dashboard (4 tabs)
├── utils/
│   ├── __init__.py
│   ├── calculations.py       # Pure financial maths — no Streamlit calls, fully testable
│   ├── charts.py             # Plotly chart builders — returns Figure objects, no side effects
│   ├── styles.py             # Design tokens (colours, fonts), CSS injection, UI helper components
│   └── user_store.py         # In-memory user store — swap with SQLite or Postgres in production
├── .streamlit/
│   └── config.toml           # Streamlit theme — green brand colours
├── requirements.txt
└── README.md
```

---

## Getting Started

### Prerequisites
- Python 3.9+

### Install and Run

```bash
git clone https://github.com/Rarai365/finance-tracker.git
cd finance-tracker
pip install -r requirements.txt
streamlit run app.py
```

Opens at `http://localhost:8501`

---

## Deploy Free (Streamlit Community Cloud)

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Sign in with GitHub → **Create app**
4. Select this repo, branch `main`, main file `app.py`
5. Click **Deploy** — live in ~2 minutes with a public URL

---

## Design Decisions

### Separate auth pages
Each auth state (`/home`, `/login`, `/signup`, `/guest`) renders as a full-screen layout, not a nested panel. This mirrors how real web apps like Facebook and LinkedIn separate their landing, sign-in, and sign-up experiences.

### No hardcoded 0s in forms
All number inputs use `value=None` with `placeholder` text. The field appears blank until the user types a value — no pre-filled zeros to clear first.

### Mobile-safe charts
All Plotly charts use fixed heights, stable axis ranges, `uniformtext` collision prevention on donuts, and legends above charts. No `autosize=True` to prevent layout thrash on 375px screens.

### Separation of concerns
- `calculations.py` — pure functions only. No imports from Streamlit. Each function has a full docstring.
- `charts.py` — returns `go.Figure` objects. The caller decides where to render.
- `styles.py` — single source of truth for all colours and fonts. No hex values elsewhere.

---

## Roadmap

- [ ] Persistent storage (SQLite or PostgreSQL)
- [ ] Fortnightly pulse check with lightweight 2-minute re-entry
- [ ] CSV bank statement import for auto-filling expenses
- [ ] Australian CDR (Open Banking) integration
- [ ] Goal-based projections (house deposit, retirement, etc.)
- [ ] Superannuation as a dedicated asset class with franking credit adjustments

---

## Disclaimer

Educational purposes only. Not personal financial advice. Capital-market assumptions are long-run estimates, not forecasts. Consult a licensed financial adviser (AFSL) before making investment decisions.

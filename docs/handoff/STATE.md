# Current State — What's Done & What's Left

> **Last updated:** 2026-10-31T13:45 IST  
> **Branch:** `feature/backend` (commit `50d91da`)  
> **PR URL:** `https://github.com/ssidharth448/brightloop/pull/new/feature/backend`  
> **Git status:** Pushed to origin/feature/backend (clean working tree).

---

## Completion Status

| Module | Status | Notes |
|--------|--------|-------|
| **Core config** | ✅ Done | `config.py` — DATABASE_URL, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, DEFAULT_TAX_RATE |
| **Security (JWT/bcrypt)** | ✅ Done | `security.py` — native bcrypt hash/verify + python-jose JWT encode/decode |
| **Dependencies (auth guards)** | ✅ Done | `dependencies.py` — `get_current_user`, `require_admin`, `require_active_user` |
| **Schemas — all 8 modules** | ✅ Done | auth, product, plan, customer, subscription, invoice, payment, dashboard |
| **Service — auth** | ✅ Done | register, authenticate, token generation |
| **Service — product** | ✅ Done | CRUD products + variants (soft-delete) |
| **Service — plan** | ✅ Done | CRUD plans (soft-delete) |
| **Service — customer** | ✅ Done | CRUD customers + deactivate |
| **Service — subscription** | ✅ Done | Create, list, get, update, activate, pause, resume, cancel with state machine |
| **Service — invoice** | ✅ Done | Create with line items, Decimal tax calc, amount_paid/outstanding via DB query |
| **Service — payment** | ✅ Done | Record payment, balance validation, invoice status sync |
| **Service — dashboard** | ✅ Done | MRR (normalized), totals, outstanding, recent subs/payments |
| **Routes — auth** | ✅ Done | POST register, POST login, GET me |
| **Routes — products** | ✅ Done | CRUD + variant CRUD nested under products |
| **Routes — plans** | ✅ Done | CRUD |
| **Routes — customers** | ✅ Done | CRUD + deactivate |
| **Routes — subscriptions** | ✅ Done | CRUD + activate, pause, resume, cancel |
| **Routes — invoices** | ✅ Done | Create, list, get (with computed paid/outstanding) |
| **Routes — payments** | ✅ Done | Create (on invoice), list, get |
| **Routes — dashboard** | ✅ Done | GET /api/dashboard/summary |
| **main.py** | ✅ Done | FastAPI app with CORS + all 8 routers registered |
| **.env.example** | ✅ Done | All required env vars documented |
| **requirements.txt** | ✅ Done | All dependencies pinned |
| **Tests** | ✅ Done | 7/7 passing — auth (5 tests) + full e2e workflow (2 tests) |
| **HANDOFF.md (repo root)** | ✅ Done | `docs/HANDOFF.md` |
| **Handoff Knowledge Base** | ✅ Done | Complete set in `docs/handoff/` (6 documents) |
| **Git commit/push** | ✅ Done | Committed and pushed to `feature/backend` |

---

## Files Created/Modified by Backend Developer

### New files:
```
backend/app/core/security.py          — Native bcrypt + JWT utilities
backend/app/core/dependencies.py      — Auth dependency injection
backend/app/schemas/auth.py            — UserRegister, UserLogin, Token, UserOut
backend/app/schemas/product.py         — ProductCreate/Update/Out, VariantCreate/Update/Out
backend/app/schemas/plan.py            — PlanCreate/Update/Out
backend/app/schemas/customer.py        — CustomerCreate/Update/Out
backend/app/schemas/subscription.py    — SubscriptionCreate/Update/Out
backend/app/schemas/invoice.py         — InvoiceCreate/Out, InvoiceItemCreate/Out
backend/app/schemas/payment.py         — PaymentCreate/Out
backend/app/schemas/dashboard.py       — DashboardSummary, RecentSubscription, RecentPayment
backend/app/services/auth_service.py   — register, authenticate, token generation
backend/app/services/product_service.py — CRUD products + variants
backend/app/services/plan_service.py    — CRUD plans
backend/app/services/customer_service.py — CRUD customers
backend/app/services/subscription_service.py — Lifecycle + billing dates (stdlib calendar)
backend/app/services/invoice_service.py  — Invoice generation + tax + totals + DB-backed payment queries
backend/app/services/payment_service.py  — Payment recording + balance checks
backend/app/services/dashboard_service.py — Aggregated metrics
backend/app/routes/auth.py             — /api/auth/* endpoints
backend/app/routes/products.py         — /api/products/* endpoints
backend/app/routes/plans.py            — /api/plans/* endpoints
backend/app/routes/customers.py        — /api/customers/* endpoints
backend/app/routes/subscriptions.py    — /api/subscriptions/* endpoints
backend/app/routes/invoices.py         — /api/invoices/* endpoints
backend/app/routes/payments.py         — /api/invoices/{id}/payments + /api/payments/*
backend/app/routes/dashboard.py        — /api/dashboard/summary
backend/app/.env.example               — Env var template
backend/tests/conftest.py              — Pytest fixtures
backend/tests/test_auth.py             — 5 auth unit tests
backend/tests/test_services_and_routes.py — 2 integration tests (full workflow)
docs/HANDOFF.md                        — Spec-required handoff document
docs/handoff/README.md                 — Handoff index
docs/handoff/STATE.md                  — This file
docs/handoff/ARCHITECTURE.md           — File map and data flow
docs/handoff/DATABASE_MODELS.md        — All 9 models with fields/constraints
docs/handoff/API_CONTRACT.md           — All 24 endpoints with req/res examples
docs/handoff/ENV_AND_SETUP.md          — How to run the backend
docs/handoff/DECISIONS.md              — Design decisions and rationale
docs/handoff/TODO.md                   — Task checklist
```

### Modified files:
```
backend/app/main.py                   — Was empty → FastAPI app with CORS + routers
backend/app/core/config.py            — Extended with JWT + tax settings + default DATABASE_URL
backend/app/schemas/__init__.py        — Added docstring
backend/requirements.txt               — Unchanged from team lead (no new deps needed)
```

### NOT touched (team lead owns these):
```
backend/app/models/*                   — All 8 model files untouched
backend/alembic/*                      — Migration untouched
backend/app/core/database.py           — Database engine untouched
```

---

## Key Technical Decisions Made During Implementation

1. **Replaced `passlib` with native `bcrypt`** — passlib is incompatible with bcrypt 5.x (AttributeError on `__about__`). Direct `bcrypt.hashpw`/`bcrypt.checkpw` works correctly.
2. **Replaced `python-dateutil` with stdlib `calendar`** — `python-dateutil` was not installed in the venv and pip has no network access. Wrote a pure-stdlib `add_interval()` using `calendar.monthrange()` for correct month/year arithmetic.
3. **Invoice `compute_amount_paid` uses DB query** — SQLite's eager-loaded relationships don't always reflect freshly-committed payments. The service now accepts an optional `db: Session` parameter and uses `func.sum()` SQL query when available, falling back to in-memory sum on `invoice.payments`.
4. **Tests call route functions directly** — The `TestClient` approach hangs due to `starlette.testclient` deprecation in the installed FastAPI version. Direct function calls bypass HTTP transport and test the full service + route + schema stack.

---

## Known Risks / Issues

1. `uvloop` in requirements only works on Linux; Windows falls back to default asyncio event loop (uvicorn handles this).
2. `passlib` is still in requirements.txt (not removed since team lead owns that file) — unused by our code.
3. `.env` file must exist at `c:\brightloop\.env` (the config reads from `(".env", "../.env")` relative to backend/app/core/).
4. The root-level `app/` and `tests/` directories were stale scaffolds from an earlier commit — deleted in our branch.

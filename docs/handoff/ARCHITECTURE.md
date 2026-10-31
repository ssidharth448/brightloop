# Architecture & File Map

> **Last updated:** 2026-10-31T13:08 IST

---

## Project Layout

```
brightloop/
├── .env                           # Runtime env vars (NOT committed)
├── .env.example                   # Template
├── docker-compose.yml             # PostgreSQL 16 + MySQL 8 containers
├── docs/
│   ├── handoff/                   # ← THIS FOLDER — agent handoff context
│   ├── api-contract.md            # (placeholder)
│   ├── architecture.md            # (placeholder)
│   └── er-diagram.md
├── backend/
│   ├── .env.example               # Backend-specific env var template
│   ├── requirements.txt           # Python dependencies (pinned)
│   ├── alembic.ini                # Alembic config
│   ├── alembic/
│   │   ├── env.py                 # Migration runner
│   │   └── versions/
│   │       └── f4e9cd8a2e34_*.py  # Initial schema migration
│   ├── app/
│   │   ├── main.py                # ★ FastAPI app — registers all routers + CORS
│   │   ├── __init__.py
│   │   ├── core/
│   │   │   ├── config.py          # Settings from env (DATABASE_URL, SECRET_KEY, etc.)
│   │   │   ├── database.py        # SQLAlchemy engine, SessionLocal, Base, get_db
│   │   │   ├── security.py        # ★ Password hashing (bcrypt) + JWT encode/decode
│   │   │   └── dependencies.py    # ★ FastAPI Depends: get_current_user, require_admin
│   │   ├── models/                # ⚠️ TEAM LEAD OWNS — DO NOT MODIFY
│   │   │   ├── __init__.py        # Re-exports all models
│   │   │   ├── user.py            # User (admin/staff)
│   │   │   ├── product.py         # Product + ProductVariant
│   │   │   ├── plan.py            # Plan (monthly/quarterly/yearly)
│   │   │   ├── customer.py        # Customer
│   │   │   ├── subscription.py    # Subscription (state machine)
│   │   │   ├── invoice.py         # Invoice + InvoiceItem (check constraints)
│   │   │   ├── payment.py         # Payment
│   │   │   └── audit_log.py       # AuditLog
│   │   ├── schemas/               # ★ Pydantic request/response models
│   │   │   ├── auth.py
│   │   │   ├── product.py
│   │   │   ├── plan.py
│   │   │   ├── customer.py
│   │   │   ├── subscription.py
│   │   │   ├── invoice.py
│   │   │   ├── payment.py
│   │   │   └── dashboard.py
│   │   ├── services/              # ★ Business logic layer
│   │   │   ├── auth_service.py
│   │   │   ├── product_service.py
│   │   │   ├── plan_service.py
│   │   │   ├── customer_service.py
│   │   │   ├── subscription_service.py
│   │   │   ├── invoice_service.py
│   │   │   ├── payment_service.py
│   │   │   └── dashboard_service.py
│   │   ├── routes/                # ★ FastAPI route handlers (thin)
│   │   │   ├── auth.py
│   │   │   ├── products.py
│   │   │   ├── plans.py
│   │   │   ├── customers.py
│   │   │   ├── subscriptions.py
│   │   │   ├── invoices.py
│   │   │   ├── payments.py
│   │   │   └── dashboard.py
│   │   └── utils/
│   │       └── __init__.py
│   └── tests/                     # ❌ Not yet implemented
│       └── __init__.py
└── frontend/                      # React (frontend teammate owns)
```

★ = Backend developer (your) files  
⚠️ = Do not touch

---

## Data Flow

```
Client Request
    │
    ▼
  Route (routes/*.py)          ← HTTP handling, validation, error codes
    │
    ├── Depends(get_db)        ← SQLAlchemy Session injection
    ├── Depends(get_current_user) ← JWT token → User
    │
    ▼
  Service (services/*.py)      ← Business logic, state machines, calculations
    │
    ▼
  SQLAlchemy Model (models/*.py) ← ORM → PostgreSQL
    │
    ▼
  Pydantic Schema (schemas/*.py) ← Response serialization
    │
    ▼
Client Response (JSON)
```

---

## Key Dependency Chain

```
config.py  →  database.py  →  models/*
                    ↓
              dependencies.py  →  security.py
                    ↓
              routes/*  →  services/*  →  models/*
                                            ↓
                                        schemas/*
```

---

## CORS Configuration

Allowed origins (in `main.py`):
- `http://localhost:5173` (Vite dev server)
- `http://localhost:3000`
- `http://127.0.0.1:5173`
- `http://127.0.0.1:3000`

---

## Authentication Flow

```
1. POST /api/auth/register  →  bcrypt hash  →  User in DB
2. POST /api/auth/login     →  verify hash  →  JWT token (sub=user.id, role=user.role)
3. Any protected endpoint   →  Bearer token in Authorization header
                            →  decode JWT  →  load User from DB  →  inject via Depends
```

JWT payload: `{"sub": "<user_id>", "role": "admin|staff", "exp": <timestamp>}`

# Brightloop Backend — Agent Handoff Index

> **Last updated:** 2026-10-31T13:08 IST  
> **Branch:** `feature/backend`  
> **Current status:** Backend implementation ~85% complete. All services, schemas, and routes written. Missing: tests, git push, runtime verification.

## Quick Start for New Agent

1. Read **[STATE.md](./STATE.md)** — current progress, what's done, what's left
2. Read **[ARCHITECTURE.md](./ARCHITECTURE.md)** — file layout, how modules connect
3. Read **[DATABASE_MODELS.md](./DATABASE_MODELS.md)** — the team lead's schema (DO NOT modify)
4. Read **[API_CONTRACT.md](./API_CONTRACT.md)** — every endpoint, request/response shapes
5. Read **[ENV_AND_SETUP.md](./ENV_AND_SETUP.md)** — how to run the backend
6. Read **[DECISIONS.md](./DECISIONS.md)** — design decisions and why
7. Read **[TODO.md](./TODO.md)** — prioritized remaining work

## Critical Rules

- **Never** create or modify SQLAlchemy models — the team lead owns `backend/app/models/`
- **Never** push directly to `main` — always use `feature/backend` → PR
- **Never** commit `.env`, credentials, or `__pycache__`
- Use `Decimal` for all money — never `float`
- Coordinate with team lead before any schema change
- Share API contract changes with frontend developer

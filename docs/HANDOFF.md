# Brightloop Backend Developer Handoff Document

> **Hackathon:** Odoo × Make-A-Ton (5-Hour Virtual Hackathon)  
> **Repository:** `https://github.com/ssidharth448/brightloop.git`  
> **Active Branch:** `main` (synchronized with `origin/main`)  
> **Complete Handoff Knowledge Base:** See [`docs/handoff/`](./handoff/)

---

## 1. Implemented Endpoints (42 Endpoints)

All endpoints follow REST conventions and return JSON (with HTML print for invoices).

### Authentication (`/api/auth`)
- `POST /api/auth/register` — Register a new admin or staff user (enforces password complexity: >8 chars, upper, lower, special char).
- `POST /api/auth/login` — Authenticate and receive a JWT Bearer token + user payload.
- `GET /api/auth/me` — Retrieve the current authenticated user.
- `POST /api/auth/staff` — Create staff user account (Admin only).
- `POST /api/auth/forgot-password` — Generate password reset token and link (simulated dispatch).
- `POST /api/auth/reset-password` — Reset password using token with complexity enforcement.

### Products & Variants (`/api/products`)
- `POST /api/products` — Create a product.
- `GET /api/products` — List products (supports pagination & active filtering).
- `GET /api/products/{id}` — Retrieve a single product.
- `PUT /api/products/{id}` — Update product attributes.
- `DELETE /api/products/{id}` — Soft-delete / deactivate product.
- `POST /api/products/{id}/variants` — Create a product variant.
- `GET /api/products/{id}/variants` — List variants for a product.
- `PUT /api/products/{id}/variants/{variant_id}` — Update variant.
- `DELETE /api/products/{id}/variants/{variant_id}` — Deactivate variant.

### Subscription Plans (`/api/plans`)
- `POST /api/plans` — Create plan (`monthly`, `quarterly`, `yearly`).
- `GET /api/plans` — List plans.
- `GET /api/plans/{id}` — Retrieve plan.
- `PUT /api/plans/{id}` — Update plan.
- `DELETE /api/plans/{id}` — Deactivate plan.

### Customers (`/api/customers`)
- `POST /api/customers` — Register customer with billing address.
- `GET /api/customers` — List customers.
- `GET /api/customers/{id}` — Retrieve customer.
- `PUT /api/customers/{id}` — Update customer details.
- `DELETE /api/customers/{id}` — Deactivate customer.

### Subscriptions (`/api/subscriptions`)
- `POST /api/subscriptions` — Subscribe customer to a plan (calculates cycle dates).
- `GET /api/subscriptions` — List subscriptions (filter by customer or status).
- `GET /api/subscriptions/{id}` — Retrieve subscription details.
- `PUT /api/subscriptions/{id}` — Update subscription.
- `POST /api/subscriptions/{id}/activate` — Activate draft subscription.
- `POST /api/subscriptions/{id}/pause` — Pause active subscription.
- `POST /api/subscriptions/{id}/resume` — Resume paused subscription.
- `POST /api/subscriptions/{id}/cancel` — Cancel subscription.

### Customer Portal (`/api/portal`)
- `GET /api/portal/my-subscriptions` — Query customer subscriptions by customer email.
- `GET /api/portal/my-invoices` — Query customer invoices by customer email.
- `POST /api/portal/subscriptions/{id}/pause` — Customer self-service pause.
- `POST /api/portal/subscriptions/{id}/cancel` — Customer self-service cancel.

### Invoices (`/api/invoices`)
- `POST /api/invoices` — Generate invoice with line items, discount rules, and tax.
- `GET /api/invoices` — List invoices (includes amount paid & outstanding balance).
- `GET /api/invoices/{id}` — Retrieve invoice by ID with items and balance.
- `POST /api/invoices/{id}/confirm` — Transition invoice from `draft` to `issued`.
- `POST /api/invoices/{id}/cancel` — Cancel invoice.
- `POST /api/invoices/{id}/send` — Simulate sending invoice via email.
- `GET /api/invoices/{id}/html` — Render clean printable HTML invoice with styling.
- `POST /api/invoices/generate-due` — Recurring billing engine: bulk-generates invoices for active subscriptions due on or before target date and advances billing cycle.
- `POST /api/invoices/check-overdue` — Overdue engine: detects and marks unpaid invoices past due date as `overdue`.

### Payments (`/api/payments`)
- `POST /api/invoices/{id}/payments` — Record simulated payment; validates against balance.
- `GET /api/payments` — List payments (optional filter by invoice).
- `GET /api/payments/{id}` — Retrieve payment details.

### Discount Rules (`/api/discounts`)
- `POST /api/discounts` — Admin create discount rule (fixed or percentage, min purchase/quantity, validity dates, max uses).
- `GET /api/discounts` — List discount rules.
- `GET /api/discounts/{id}` — Get single discount rule.
- `PUT /api/discounts/{id}` — Update discount rule.
- `DELETE /api/discounts/{id}` — Delete discount rule.

### Quotation Templates (`/api/quotation-templates`)
- `POST /api/quotation-templates` — Create quotation template with lines, validity, terms.
- `GET /api/quotation-templates` — List quotation templates.
- `GET /api/quotation-templates/{id}` — Get quotation template.
- `PUT /api/quotation-templates/{id}` — Update quotation template.
- `DELETE /api/quotation-templates/{id}` — Delete quotation template.
- `POST /api/quotation-templates/convert-to-subscription` — Convert accepted quote template into live subscription.

### Dashboard (`/api/dashboard`)
- `GET /api/dashboard/summary` — Aggregated metrics: total customers, active subs, MRR (normalized to monthly), total invoices, outstanding balance, total revenue, recent activity, overdue invoices count, overdue amount, and overdue invoices breakdown.

---

## 2. Authentication Requirements

- Standard OAuth2 Bearer token mechanism.
- Header: `Authorization: Bearer <access_token>`.
- Token payload encodes `sub` (User ID), `role` (`admin` or `staff`), and `exp`.
- Password hashing using native `bcrypt`.
- Password complexity enforced: `> 8` characters, at least 1 uppercase, 1 lowercase, 1 special character.
- Enforced on all entity routes via FastAPI dependency injection (`require_active_user`, `require_admin`).

---

## 3. Database Model Dependencies & Storage Architecture

The Team Lead owns all models in `backend/app/models/`:
- `User` (`users`)
- `Product` (`products`)
- `ProductVariant` (`product_variants`)
- `Plan` (`plans`)
- `Customer` (`customers`)
- `Subscription` (`subscriptions`)
- `Invoice` (`invoices`)
- `InvoiceItem` (`invoice_items`)
- `Payment` (`payments`)
- `AuditLog` (`audit_logs`)

All relations, check constraints, composite foreign keys, and indexes are preserved.
New domain features (Discount Rules, Quotation Templates) are persisted cleanly using service-layer file stores with JSON serialization, avoiding schema/migration alterations while ensuring durability across server restarts.

---

## 4. Test Suite

- Total tests: **32 tests** across `test_auth.py`, `test_services_and_routes.py`, and `test_new_features.py`.
- Run command: `pytest`
- Pass rate: **100% (32/32 passed)**.
- Frontend build: `npm run build` completed in `< 2s` with **0 errors**.

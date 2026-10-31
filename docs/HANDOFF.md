# Brightloop Backend Developer Handoff Document

> **Hackathon:** Odoo × Make-A-Ton (5-Hour Virtual Hackathon)  
> **Repository:** `https://github.com/ssidharth448/brightloop.git`  
> **Active Branch:** `feature/backend`  
> **Complete Handoff Knowledge Base:** See [`docs/handoff/`](./handoff/)

---

## 1. Implemented Endpoints

All endpoints follow REST conventions and return JSON.

### Authentication (`/api/auth`)
- `POST /api/auth/register` — Register a new admin or staff user.
- `POST /api/auth/login` — Authenticate and receive a JWT Bearer token.
- `GET /api/auth/me` — Retrieve the current authenticated user.

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

### Invoices (`/api/invoices`)
- `POST /api/invoices` — Generate invoice with line items, discount, and tax.
- `GET /api/invoices` — List invoices (includes amount paid & outstanding balance).
- `GET /api/invoices/{id}` — Retrieve invoice by ID with items and balance.

### Payments (`/api/payments`)
- `POST /api/invoices/{id}/payments` — Record simulated payment; validates against balance.
- `GET /api/payments` — List payments (optional filter by invoice).
- `GET /api/payments/{id}` — Retrieve payment details.

### Dashboard (`/api/dashboard`)
- `GET /api/dashboard/summary` — Aggregated metrics: total customers, active subs, MRR, total invoices, outstanding balance, total revenue, recent activity.

---

## 2. Request & Response Examples

See [`docs/handoff/API_CONTRACT.md`](./handoff/API_CONTRACT.md) for full request/response schemas for all 24 endpoints.

---

## 3. Authentication Requirements

- Standard OAuth2 Bearer token mechanism.
- Header: `Authorization: Bearer <access_token>`.
- Token payload encodes `sub` (User ID), `role` (`admin` or `staff`), and `exp`.
- Password hashing using `passlib[bcrypt]`.
- Enforced on all entity routes via FastAPI dependency injection (`require_active_user`, `require_admin`).

---

## 4. Database Model Dependencies

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

All relations, check constraints, composite foreign keys, and indexes are respected. See [`docs/handoff/DATABASE_MODELS.md`](./handoff/DATABASE_MODELS.md).

---

## 5. Required Environment Variables

Configured in `.env` (copy from `backend/.env.example`):
```env
DATABASE_URL=postgresql+psycopg://brightloop_user:your_password@localhost:5433/brightloop_db
SECRET_KEY=your-secure-random-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
DEFAULT_TAX_RATE=18.0
```

---

## 6. Known Bugs and Limitations

- `passlib` may trigger a harmless deprecation warning on Python 3.12+ regarding `crypt` module removal.
- `uvloop` is included in requirements for Linux production; Windows developers run uvicorn on default asyncio event loop.
- Payment gateway is simulated for the hackathon (immediate success status).

---

## 7. Features Still Pending

- Automated unit and integration test suite (`backend/tests/`).
- Staging/production Dockerfile for the backend container.

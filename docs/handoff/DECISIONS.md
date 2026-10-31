# Architectural & Business Logic Decisions

> **Context:** 5-hour virtual hackathon (Odoo x Make-A-Ton). Modular monolith architecture.

---

## 1. Monetary Precision: `Decimal` Everywhere
- **Problem:** Floating point numbers introduce rounding errors (e.g. `0.1 + 0.2 = 0.30000000000000004`).
- **Decision:** Every monetary amount (prices, subtotals, taxes, discounts, totals, balances, payments, MRR) uses Python's `Decimal` with 2 decimal places (`Decimal("0.01")`) and `ROUND_HALF_UP`.
- **Database:** SQLAlchemy `Numeric(12, 2)` columns.

## 2. Subscription Lifecycle & State Machine
- **Valid States:** `draft`, `active`, `paused`, `cancelled`, `expired`
- **Transitions Allowed:**
  - `draft` -> `active`, `cancelled`
  - `active` -> `paused`, `cancelled`, `expired`
  - `paused` -> `active`, `cancelled`
  - `cancelled` -> None (terminal state)
  - `expired` -> None (terminal state)
- **Billing End Calculation:**
  - Used `python-dateutil.relativedelta` instead of hardcoded 30/90/365 days.
  - Correctly accounts for calendar month lengths, leap years, and exact date shifts.
- **Trial Days:**
  - If a plan has `trial_days > 0`, the billing period start is offset by `trial_days`.

## 3. Invoice Calculation & Check Constraints Compliance
- The Team Lead's database schema includes strict check constraints on `invoices`:
  - `subtotal >= 0 AND discount_amount >= 0 AND tax_amount >= 0 AND total_amount >= 0`
  - `discount_amount <= subtotal`
  - `total_amount = subtotal - discount_amount + tax_amount`
  - `due_date >= issue_date`
  - `fk_invoice_subscription_customer`: Composite foreign key `[subscription_id, customer_id]` -> `[subscriptions.id, subscriptions.customer_id]`
- **Decision:** The service computes exact values before inserting to ensure the check constraint `total_amount = subtotal - discount_amount + tax_amount` always evaluates to true down to the cent.
- Invoices can be independent or linked to a subscription.

## 4. Payment Simulation & Invoice Status Sync
- No external payment gateway is required for this hackathon.
- **Rule:** A payment cannot exceed the current outstanding balance (`total_amount - sum(succeeded payments)`).
- **Status Progression:**
  - Payment recorded with status `"succeeded"`.
  - If total paid == `total_amount` -> Invoice status becomes `"paid"`.
  - If total paid > 0 and < `total_amount` -> Invoice status becomes `"partially_paid"`.

## 5. MRR Normalization Formula
Per project requirements:
- Monthly plan: `price`
- Quarterly plan: `price / 3`
- Yearly plan: `price / 12`
- **Rule:** Only subscriptions with status `"active"` contribute to MRR. Paused, cancelled, expired, and draft subscriptions are excluded.

## 6. Authentication & Roles
- Standard OAuth2 password flow with JWT Bearer tokens.
- Passwords hashed with `passlib` using bcrypt.
- Roles supported in schema: `"admin"`, `"staff"`.
- Token expiry configured to 60 minutes.

# Database Models Reference

> **Important:** The Team Lead owns database models and migrations (`backend/app/models/*` and `backend/alembic/*`).
> **DO NOT** modify, delete, or create duplicate SQLAlchemy models without coordinating with the Team Lead.

---

## 1. User (`app.models.user.User`)
**Table:** `users`

| Column | Type | Constraints / Defaults | Description |
|---|---|---|---|
| `id` | Integer | Primary Key | User unique ID |
| `name` | String(100) | Not Null | User full name |
| `email` | String(255) | Not Null, Unique | Email address for login |
| `password_hash` | String(255) | Not Null | Bcrypt hashed password |
| `role` | String(20) | Not Null, Default `"staff"`, Check `role IN ('admin', 'staff')` | Access role |
| `is_active` | Boolean | Not Null, Default `True` | Active status |
| `created_at` | DateTime(tz) | Not Null, Default UTC now | Timestamp |
| `updated_at` | DateTime(tz) | Not Null, Default/OnUpdate UTC now | Timestamp |

**Relationships:**
- `audit_logs`: 1-to-many with `AuditLog`

---

## 2. Product (`app.models.product.Product`)
**Table:** `products`

| Column | Type | Constraints / Defaults | Description |
|---|---|---|---|
| `id` | Integer | Primary Key | Product ID |
| `name` | String(150) | Not Null | Product name |
| `description` | Text | Nullable | Details/description |
| `category` | String(100) | Nullable | Category tag |
| `is_active` | Boolean | Not Null, Default `True` | Soft-deletion flag |
| `created_at` | DateTime(tz) | Not Null, Default UTC now | Timestamp |

**Relationships:**
- `variants`: 1-to-many with `ProductVariant`
- `plans`: 1-to-many with `Plan`

---

## 3. ProductVariant (`app.models.product.ProductVariant`)
**Table:** `product_variants`

| Column | Type | Constraints / Defaults | Description |
|---|---|---|---|
| `id` | Integer | Primary Key | Variant ID |
| `product_id` | Integer | ForeignKey(`products.id`, ondelete="RESTRICT"), Index | Parent product |
| `name` | String(100) | Not Null | Variant title/name |
| `sku` | String(80) | Nullable, Unique | Stock Keeping Unit |
| `description` | Text | Nullable | Variant description |
| `is_active` | Boolean | Not Null, Default `True` | Active flag |
| `created_at` | DateTime(tz) | Not Null, Default UTC now | Timestamp |

**Table Constraints:**
- `UniqueConstraint("product_id", "name", name="uq_variant_product_name")`
- `UniqueConstraint("product_id", "id", name="uq_variant_product_id_id")`

**Relationships:**
- `product`: Many-to-1 with `Product`
- `plans`: 1-to-many with `Plan` (viewonly=True)

---

## 4. Plan (`app.models.plan.Plan`)
**Table:** `plans`

| Column | Type | Constraints / Defaults | Description |
|---|---|---|---|
| `id` | Integer | Primary Key | Plan ID |
| `product_id` | Integer | ForeignKey(`products.id`, ondelete="RESTRICT"), Index | Base product |
| `variant_id` | Integer | Nullable, Index | Optional variant |
| `name` | String(150) | Not Null | Plan name |
| `description` | Text | Nullable | Description |
| `price` | Numeric(12, 2)| Not Null | Plan recurring price |
| `currency` | String(3) | Not Null, Default `"INR"`, Length=3 | Currency code |
| `billing_interval` | String(20) | Not Null | `'monthly'`, `'quarterly'`, or `'yearly'` |
| `trial_days` | Integer | Not Null, Default `0`, `trial_days >= 0` | Free trial length |
| `is_active` | Boolean | Not Null, Default `True` | Status |
| `created_at` | DateTime(tz) | Not Null, Default UTC now | Timestamp |

**Table Constraints:**
- `ck_plan_price_nonnegative`: `price >= 0`
- `ck_plan_billing_interval`: `billing_interval IN ('monthly', 'quarterly', 'yearly')`
- `ck_plan_trial_days_nonnegative`: `trial_days >= 0`
- `ck_plan_currency_length`: `length(currency) = 3`
- `fk_plan_variant_belongs_to_product`: Composite foreign key `[product_id, variant_id]` -> `[product_variants.product_id, product_variants.id]`

**Relationships:**
- `product`: Many-to-1 with `Product`
- `variant`: Many-to-1 with `ProductVariant` (viewonly=True)

---

## 5. Customer (`app.models.customer.Customer`)
**Table:** `customers`

| Column | Type | Constraints / Defaults | Description |
|---|---|---|---|
| `id` | Integer | Primary Key | Customer ID |
| `name` | String(150) | Not Null | Customer full name |
| `email` | String(255) | Not Null, Unique, Index | Email address |
| `phone` | String(30) | Nullable | Phone number |
| `billing_address` | Text | Nullable | Address line |
| `city` | String(100) | Nullable | City |
| `state` | String(100) | Nullable | State/Region |
| `postal_code` | String(20) | Nullable | Postal/ZIP |
| `country` | String(100) | Not Null, Default `"India"` | Country name |
| `is_active` | Boolean | Not Null, Default `True` | Status |
| `created_at` | DateTime(tz) | Not Null, Default UTC now | Timestamp |
| `updated_at` | DateTime(tz) | Not Null, Default/OnUpdate UTC now | Timestamp |

**Relationships:**
- `subscriptions`: 1-to-many with `Subscription`
- `invoices`: 1-to-many with `Invoice`

---

## 6. Subscription (`app.models.subscription.Subscription`)
**Table:** `subscriptions`

| Column | Type | Constraints / Defaults | Description |
|---|---|---|---|
| `id` | Integer | Primary Key | Subscription ID |
| `customer_id` | Integer | ForeignKey(`customers.id`, ondelete="RESTRICT"), Index | Customer reference |
| `plan_id` | Integer | ForeignKey(`plans.id`, ondelete="RESTRICT"), Index | Plan reference |
| `status` | String(20) | Not Null, Default `"draft"`, Index | Status state machine |
| `start_date` | Date | Not Null | Effective start date |
| `current_period_start` | Date | Not Null | Current billing cycle start |
| `current_period_end` | Date | Not Null | Current cycle end (`> current_period_start`) |
| `next_billing_date` | Date | Nullable, Index | Next scheduled billing date |
| `cancel_at_period_end` | Boolean | Not Null, Default `False` | Auto-cancel at cycle end flag |
| `cancelled_at` | DateTime(tz) | Nullable | Cancellation timestamp |
| `created_at` | DateTime(tz) | Not Null, Default UTC now | Timestamp |
| `updated_at` | DateTime(tz) | Not Null, Default/OnUpdate UTC now | Timestamp |

**Table Constraints:**
- `ck_subscription_status`: `status IN ('draft', 'active', 'paused', 'cancelled', 'expired')`
- `ck_subscription_period_dates`: `current_period_end > current_period_start`
- `uq_subscription_id_customer_id`: Unique `(id, customer_id)` (used for composite invoice constraint)

**State Machine Transitions:**
- `draft` -> `active`, `cancelled`
- `active` -> `paused`, `cancelled`, `expired`
- `paused` -> `active`, `cancelled`
- `cancelled` -> [TERMINAL]
- `expired` -> [TERMINAL]

---

## 7. Invoice & InvoiceItem (`app.models.invoice.Invoice`, `InvoiceItem`)
**Table:** `invoices`

| Column | Type | Constraints / Defaults | Description |
|---|---|---|---|
| `id` | Integer | Primary Key | Invoice ID |
| `invoice_number` | String(50) | Not Null, Unique | Unique code (e.g. `INV-XXXXXX`) |
| `customer_id` | Integer | ForeignKey(`customers.id`, ondelete="RESTRICT"), Index | Customer reference |
| `subscription_id` | Integer | Nullable, Index | Optional subscription link |
| `issue_date` | Date | Not Null | Issue date |
| `due_date` | Date | Not Null, `due_date >= issue_date` | Payment due date |
| `currency` | String(3) | Not Null, Default `"INR"` | Currency ISO code |
| `subtotal` | Numeric(12, 2)| Not Null | Sum of item lines |
| `discount_amount` | Numeric(12, 2)| Not Null, Default `0.00` | Discount subtracted |
| `tax_amount` | Numeric(12, 2)| Not Null, Default `0.00` | Tax added |
| `total_amount` | Numeric(12, 2)| Not Null | `subtotal - discount_amount + tax_amount` |
| `status` | String(20) | Not Null, Default `"draft"`, Index | Status |
| `created_at` | DateTime(tz) | Not Null, Default UTC now | Timestamp |

**Table Constraints:**
- `ck_invoice_status`: `status IN ('draft', 'issued', 'partially_paid', 'paid', 'overdue', 'cancelled')`
- `ck_invoice_amounts_nonnegative`: all amounts `>= 0`
- `ck_invoice_discount_limit`: `discount_amount <= subtotal`
- `ck_invoice_total_calculation`: `total_amount = subtotal - discount_amount + tax_amount`
- `ck_invoice_due_date`: `due_date >= issue_date`
- `fk_invoice_subscription_customer`: Composite foreign key `[subscription_id, customer_id]` -> `[subscriptions.id, subscriptions.customer_id]`

**Table:** `invoice_items`

| Column | Type | Constraints / Defaults | Description |
|---|---|---|---|
| `id` | Integer | Primary Key | Item ID |
| `invoice_id` | Integer | ForeignKey(`invoices.id`, ondelete="CASCADE"), Index | Parent invoice |
| `description` | String(255) | Not Null | Snapshot line item text |
| `quantity` | Integer | Not Null, Default 1, `quantity > 0` | Count |
| `unit_price` | Numeric(12, 2)| Not Null, `>= 0` | Price per unit |
| `line_total` | Numeric(12, 2)| Not Null, `>= 0` | `quantity * unit_price` |

---

## 8. Payment (`app.models.payment.Payment`)
**Table:** `payments`

| Column | Type | Constraints / Defaults | Description |
|---|---|---|---|
| `id` | Integer | Primary Key | Payment ID |
| `invoice_id` | Integer | ForeignKey(`invoices.id`, ondelete="RESTRICT"), Index | Invoice reference |
| `amount` | Numeric(12, 2)| Not Null, `amount > 0` | Paid amount |
| `payment_method` | String(30) | Not Null | `'cash'`, `'card'`, `'bank_transfer'`, or `'upi'` |
| `status` | String(20) | Not Null, Default `"pending"`, Index | `'pending'`, `'succeeded'`, `'failed'`, `'refunded'` |
| `transaction_reference`| String(100) | Nullable, Unique | Sim reference / transaction ID |
| `paid_at` | DateTime(tz) | Nullable | Payment confirmation timestamp |
| `created_at` | DateTime(tz) | Not Null, Default UTC now | Timestamp |

---

## 9. AuditLog (`app.models.audit_log.AuditLog`)
**Table:** `audit_logs`

| Column | Type | Constraints / Defaults | Description |
|---|---|---|---|
| `id` | Integer | Primary Key | Log ID |
| `user_id` | Integer | ForeignKey(`users.id`, ondelete="SET NULL"), Nullable, Index | Actor user |
| `action` | String(100) | Not Null | Action verb (e.g. `"create"`) |
| `entity_type` | String(100) | Not Null | Target entity (e.g. `"subscription"`) |
| `entity_id` | Integer | Nullable | Target ID |
| `details` | JSON | Nullable | Arbitrary payload metadata |
| `created_at` | DateTime(tz) | Not Null, Default UTC now, Index | Log timestamp |

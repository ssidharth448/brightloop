# API Contract & Specifications

> **Base URL:** `http://localhost:8000`  
> **Interactive Docs (Swagger):** `http://localhost:8000/docs`  
> **OpenAPI JSON:** `http://localhost:8000/openapi.json`  

---

## Authentication

All protected endpoints require HTTP Header:
```http
Authorization: Bearer <access_token>
```

### 1. Register User
`POST /api/auth/register`
- **Auth:** Public
- **Request Body:**
```json
{
  "name": "Admin User",
  "email": "admin@example.com",
  "password": "secretpassword",
  "role": "admin"
}
```
- **Responses:**
  - `201 Created`:
```json
{
  "id": 1,
  "name": "Admin User",
  "email": "admin@example.com",
  "role": "admin",
  "is_active": true,
  "created_at": "2026-10-31T07:30:00Z",
  "updated_at": "2026-10-31T07:30:00Z"
}
```
  - `409 Conflict`: Email already exists.

---

### 2. Login
`POST /api/auth/login`
- **Auth:** Public
- **Request Body:**
```json
{
  "email": "admin@example.com",
  "password": "secretpassword"
}
```
- **Responses:**
  - `200 OK`:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```
  - `401 Unauthorized`: Invalid credentials.

---

### 3. Current User
`GET /api/auth/me`
- **Auth:** Bearer Token required
- **Response:**
  - `200 OK`: `UserOut` object

---

## Products & Product Variants

### 4. Create Product
`POST /api/products`
- **Auth:** Active user
- **Request:**
```json
{
  "name": "Brightloop CRM",
  "description": "Full cloud CRM suite",
  "category": "SaaS",
  "is_active": true
}
```
- **Response:** `201 Created` -> ProductOut

### 5. List Products
`GET /api/products?skip=0&limit=100&active_only=false`
- **Auth:** Active user
- **Response:** `200 OK` -> `list[ProductOut]`

### 6. Get Product by ID
`GET /api/products/{id}`
- **Auth:** Active user
- **Response:** `200 OK` or `404 Not Found`

### 7. Update Product
`PUT /api/products/{id}`
- **Auth:** Active user
- **Request:**
```json
{
  "name": "Brightloop CRM Pro",
  "description": "Updated description",
  "is_active": true
}
```
- **Response:** `200 OK` or `404 Not Found`

### 8. Deactivate Product
`DELETE /api/products/{id}`
- **Auth:** Active user
- **Response:** `204 No Content` (Soft-deactivates product)

### 9. Create Product Variant
`POST /api/products/{id}/variants`
- **Auth:** Active user
- **Request:**
```json
{
  "name": "Enterprise 50-Seat",
  "sku": "CRM-ENT-50",
  "description": "50 user licenses",
  "is_active": true
}
```
- **Response:** `201 Created` or `409 Conflict` (duplicate SKU/name)

### 10. List Product Variants
`GET /api/products/{id}/variants?active_only=false`
- **Auth:** Active user
- **Response:** `200 OK` -> `list[VariantOut]`

### 11. Update Product Variant
`PUT /api/products/{id}/variants/{variant_id}`
- **Auth:** Active user
- **Response:** `200 OK` or `404 Not Found`

### 12. Deactivate Product Variant
`DELETE /api/products/{id}/variants/{variant_id}`
- **Auth:** Active user
- **Response:** `204 No Content`

---

## Subscription Plans

### 13. Create Plan
`POST /api/plans`
- **Auth:** Active user
- **Request:**
```json
{
  "product_id": 1,
  "variant_id": null,
  "name": "Pro Monthly",
  "description": "Billed each month",
  "price": "999.00",
  "currency": "INR",
  "billing_interval": "monthly",
  "trial_days": 14,
  "is_active": true
}
```
- **Valid `billing_interval` values:** `"monthly"`, `"quarterly"`, `"yearly"`
- **Response:** `201 Created` -> PlanOut

### 14. List Plans
`GET /api/plans?skip=0&limit=100&active_only=false`
- **Auth:** Active user
- **Response:** `200 OK` -> `list[PlanOut]`

### 15. Get / Update / Delete Plan
- `GET /api/plans/{id}` -> `200 OK`
- `PUT /api/plans/{id}` -> `200 OK`
- `DELETE /api/plans/{id}` -> `204 No Content` (soft-deactivates)

---

## Customers

### 16. Register Customer
`POST /api/customers`
- **Auth:** Active user
- **Request:**
```json
{
  "name": "Acme Corp",
  "email": "billing@acme.com",
  "phone": "+91 9876543210",
  "billing_address": "123 Tech Park, MG Road",
  "city": "Bengaluru",
  "state": "Karnataka",
  "postal_code": "560001",
  "country": "India"
}
```
- **Response:** `201 Created` or `409 Conflict` (duplicate email)

### 17. List / Get / Update / Deactivate Customers
- `GET /api/customers?skip=0&limit=100&active_only=false` -> `200 OK`
- `GET /api/customers/{id}` -> `200 OK`
- `PUT /api/customers/{id}` -> `200 OK`
- `DELETE /api/customers/{id}` -> `204 No Content`

---

## Subscriptions Lifecycle

### 18. Create Subscription
`POST /api/subscriptions`
- **Auth:** Active user
- **Request:**
```json
{
  "customer_id": 1,
  "plan_id": 1,
  "start_date": "2026-10-31"
}
```
- **Lifecycle Logic:**
  - Auto-computes `current_period_start` and `current_period_end` using `relativedelta` based on `billing_interval` (`monthly` = +1 mo, `quarterly` = +3 mo, `yearly` = +1 yr).
  - Honors `trial_days` from the Plan.
  - Initial status: `"active"`.
- **Response:** `201 Created` -> `SubscriptionOut`

### 19. List Subscriptions
`GET /api/subscriptions?skip=0&limit=100&customer_id=1&status=active`
- **Auth:** Active user
- **Response:** `200 OK` -> `list[SubscriptionOut]`

### 20. Lifecycle State Transitions
- `POST /api/subscriptions/{id}/pause`
  - Valid only from: `active`
  - Status becomes: `paused` (`next_billing_date` set to null)
- `POST /api/subscriptions/{id}/resume`
  - Valid only from: `paused`
  - Status becomes: `active` (recomputes cycle from today)
- `POST /api/subscriptions/{id}/cancel`
  - Valid from: `draft`, `active`, `paused`
  - Status becomes: `cancelled` (`cancelled_at` set to UTC now)

---

## Invoices & Payments

### 21. Create Invoice
`POST /api/invoices`
- **Auth:** Active user
- **Request:**
```json
{
  "customer_id": 1,
  "subscription_id": 1,
  "issue_date": "2026-10-31",
  "due_date": "2026-11-30",
  "currency": "INR",
  "items": [
    {
      "description": "Pro Monthly Subscription",
      "quantity": 1,
      "unit_price": "999.00"
    }
  ],
  "discount_amount": "99.00",
  "tax_rate": "18.0"
}
```
- **Calculation Details:**
  - `subtotal = sum(unit_price * quantity)`
  - `tax_amount = (subtotal - discount_amount) * (tax_rate / 100)`
  - `total_amount = subtotal - discount_amount + tax_amount`
  - Stored and computed strictly with `Decimal`.
- **Response:** `201 Created` -> `InvoiceOut` with `amount_paid` and `outstanding_balance`.

### 22. List / Get Invoices
- `GET /api/invoices?skip=0&limit=100&customer_id=1&status=issued`
- `GET /api/invoices/{id}`
  - Returns `amount_paid` and `outstanding_balance`.

### 23. Record Payment
`POST /api/invoices/{id}/payments`
- **Auth:** Active user
- **Request:**
```json
{
  "amount": "500.00",
  "payment_method": "upi",
  "transaction_reference": "UPI-SIM-849202"
}
```
- **Validation & Rules:**
  - `payment_method` in `['cash', 'card', 'bank_transfer', 'upi']`
  - Prevents payments greater than `outstanding_balance`.
  - Automatically transitions invoice to `"partially_paid"` or `"paid"`.
- **Response:** `201 Created` -> `PaymentOut`

---

## Dashboard

### 24. Summary
`GET /api/dashboard/summary`
- **Auth:** Active user
- **Response:**
```json
{
  "total_customers": 12,
  "active_subscriptions": 9,
  "monthly_recurring_revenue": "8991.00",
  "total_invoices": 15,
  "outstanding_invoice_amount": "1450.00",
  "total_payments_received": "18400.00",
  "recent_subscriptions": [
    {
      "id": 5,
      "customer_name": "Acme Corp",
      "plan_name": "Pro Monthly",
      "status": "active",
      "start_date": "2026-10-31",
      "created_at": "2026-10-31T07:35:00Z"
    }
  ],
  "recent_payments": [
    {
      "id": 8,
      "invoice_number": "INV-A1B2C3D4",
      "amount": "500.00",
      "payment_method": "upi",
      "status": "succeeded",
      "paid_at": "2026-10-31T07:40:00Z",
      "created_at": "2026-10-31T07:40:00Z"
    }
  ]
}
```
- **MRR Normalization:**
  - `monthly` price = `price`
  - `quarterly` price = `price / 3`
  - `yearly` price = `price / 12`
  - Excludes paused, cancelled, draft, or expired subscriptions.

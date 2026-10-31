// Central place for every shape the app uses.
// When the backend contract is confirmed, fix field names HERE (and in services/realApi.ts).

export type ID = string | number

export type BillingInterval = 'weekly' | 'monthly' | 'quarterly' | 'yearly'
export type SubscriptionStatus = 'draft' | 'active' | 'paused' | 'cancelled' | 'expired'
export type InvoiceStatus = 'unpaid' | 'partial' | 'paid' | 'void'
export type PaymentMethod = 'card' | 'upi' | 'bank_transfer' | 'cash'
export type PaymentStatus = 'succeeded' | 'pending' | 'failed'

export interface User {
  id: ID
  email: string
  name: string
}

export interface Variant {
  id: ID
  name: string
  sku: string
  extra_price: number
}

export interface Product {
  id: ID
  name: string
  description: string
  base_price: number
  active: boolean
  variants: Variant[]
  created_at: string
}

export interface Plan {
  id: ID
  name: string
  product_id: ID
  product_name: string
  price: number
  interval: BillingInterval
  active: boolean
}

export interface Customer {
  id: ID
  name: string
  email: string
  phone: string
  company: string
  created_at: string
}

export interface Subscription {
  id: ID
  customer_id: ID
  customer_name: string
  plan_id: ID
  plan_name: string
  price: number
  interval: BillingInterval
  start_date: string
  next_billing_date: string
  status: SubscriptionStatus
}

export interface Invoice {
  id: ID
  number: string
  subscription_id: ID
  customer_id: ID
  customer_name: string
  issue_date: string
  due_date: string
  subtotal: number
  discount: number
  tax: number
  total: number
  amount_paid: number
  balance: number
  status: InvoiceStatus
}

export interface Payment {
  id: ID
  invoice_id: ID
  invoice_number: string
  customer_name: string
  amount: number
  method: PaymentMethod
  status: PaymentStatus
  paid_at: string
}

export interface DashboardSummary {
  total_customers: number
  active_subscriptions: number
  mrr: number
  total_invoices: number
  outstanding_amount: number
  recent_payments: Payment[]
  recent_subscriptions: Subscription[]
}

// ---- Form payloads ----
export interface ProductInput { name: string; description: string; base_price: number; active: boolean }
export interface VariantInput { name: string; sku: string; extra_price: number }
export interface PlanInput { name: string; product_id: ID; price: number; interval: BillingInterval; active: boolean }
export interface CustomerInput { name: string; email: string; phone: string; company: string }
export interface SubscriptionInput { customer_id: ID; plan_id: ID; start_date: string }
export interface PaymentInput { amount: number; method: PaymentMethod }

// ---- The contract both realApi.ts and mockApi.ts implement ----
export interface ApiService {
  login(email: string, password: string): Promise<{ token: string; user: User }>
  me(): Promise<User>
  dashboard(): Promise<DashboardSummary>
  products: {
    list(): Promise<Product[]>
    get(id: ID): Promise<Product>
    create(data: ProductInput): Promise<Product>
    update(id: ID, data: Partial<ProductInput>): Promise<Product>
    remove(id: ID): Promise<void>
    addVariant(productId: ID, data: VariantInput): Promise<Product>
    updateVariant(productId: ID, variantId: ID, data: Partial<VariantInput>): Promise<Product>
    removeVariant(productId: ID, variantId: ID): Promise<Product>
  }
  plans: {
    list(): Promise<Plan[]>
    get(id: ID): Promise<Plan>
    create(data: PlanInput): Promise<Plan>
    update(id: ID, data: Partial<PlanInput>): Promise<Plan>
    setActive(id: ID, active: boolean): Promise<Plan>
  }
  customers: {
    list(): Promise<Customer[]>
    get(id: ID): Promise<Customer>
    create(data: CustomerInput): Promise<Customer>
    update(id: ID, data: Partial<CustomerInput>): Promise<Customer>
  }
  subscriptions: {
    list(): Promise<Subscription[]>
    get(id: ID): Promise<Subscription>
    create(data: SubscriptionInput): Promise<Subscription>
    setStatus(id: ID, status: 'active' | 'paused' | 'cancelled'): Promise<Subscription>
  }
  invoices: {
    list(): Promise<Invoice[]>
    get(id: ID): Promise<Invoice>
    generate(subscriptionId: ID): Promise<Invoice>
    recordPayment(invoiceId: ID, data: PaymentInput): Promise<Invoice>
  }
  payments: {
    list(): Promise<Payment[]>
    get(id: ID): Promise<Payment>
  }
}

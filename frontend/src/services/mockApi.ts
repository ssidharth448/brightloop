import type {
  ApiService, BillingInterval, Customer, DashboardSummary, ID, Invoice, Payment, Plan,
  Product, Subscription, User,
} from '../types'
import { ApiError, tokenStore } from './http'

// In-memory fake backend. Data resets on page refresh.
// Demo login: admin@brightloop.com / admin123

const delay = (ms = 300) => new Promise((resolve) => setTimeout(resolve, ms))
const round2 = (n: number) => Math.round(n * 100) / 100
const clone = <T,>(value: T): T => structuredClone(value)
let seq = 100
const nextId = (prefix: string) => `${prefix}_${++seq}`

const isoDate = (d: Date) => d.toISOString().slice(0, 10)
const today = () => isoDate(new Date())
const daysFromNow = (n: number) => {
  const d = new Date()
  d.setUTCDate(d.getUTCDate() + n)
  return isoDate(d)
}
function addInterval(date: string, interval: BillingInterval): string {
  const d = new Date(date)
  if (interval === 'weekly') d.setUTCDate(d.getUTCDate() + 7)
  if (interval === 'monthly') d.setUTCMonth(d.getUTCMonth() + 1)
  if (interval === 'quarterly') d.setUTCMonth(d.getUTCMonth() + 3)
  if (interval === 'yearly') d.setUTCFullYear(d.getUTCFullYear() + 1)
  return isoDate(d)
}
const monthlyValue = (price: number, interval: BillingInterval) =>
  ({ weekly: price * 4.33, monthly: price, quarterly: price / 3, yearly: price / 12 })[interval]

// ---------- stored rows (names are joined on read, like a real backend would) ----------
type PlanRow = Omit<Plan, 'product_name'>
type SubRow = Omit<Subscription, 'customer_name' | 'plan_name' | 'price' | 'interval'>
type InvoiceRow = Omit<Invoice, 'customer_name'>
type PaymentRow = Omit<Payment, 'customer_name' | 'invoice_number'>

const db = {
  products: [
    {
      id: 'prod_1', name: 'Brightloop CRM', description: 'Customer relationship suite for small teams.',
      base_price: 1200, active: true, created_at: daysFromNow(-40),
      variants: [
        { id: 'var_1', name: 'Starter (5 seats)', sku: 'CRM-S5', extra_price: 0 },
        { id: 'var_2', name: 'Team (25 seats)', sku: 'CRM-T25', extra_price: 800 },
      ],
    },
    {
      id: 'prod_2', name: 'Support Desk', description: 'Shared inbox and ticketing.',
      base_price: 600, active: true, created_at: daysFromNow(-25), variants: [],
    },
  ] as Product[],
  plans: [
    { id: 'plan_1', name: 'CRM Monthly', product_id: 'prod_1', price: 1200, interval: 'monthly', active: true },
    { id: 'plan_2', name: 'CRM Yearly', product_id: 'prod_1', price: 12000, interval: 'yearly', active: true },
    { id: 'plan_3', name: 'Support Desk Monthly', product_id: 'prod_2', price: 600, interval: 'monthly', active: true },
  ] as PlanRow[],
  customers: [
    { id: 'cust_1', name: 'Asha Menon', email: 'asha@kaveritextiles.in', phone: '+91 98470 11223', company: 'Kaveri Textiles', created_at: daysFromNow(-30) },
    { id: 'cust_2', name: 'Rohan Iyer', email: 'rohan@palakkadfoods.in', phone: '+91 98950 44821', company: 'Palakkad Foods', created_at: daysFromNow(-18) },
    { id: 'cust_3', name: 'Meera Nair', email: 'meera@greenleaf.co', phone: '+91 94960 77310', company: 'Greenleaf Studio', created_at: daysFromNow(-6) },
  ] as Customer[],
  subscriptions: [
    { id: 'sub_1', customer_id: 'cust_1', plan_id: 'plan_1', start_date: daysFromNow(-20), next_billing_date: daysFromNow(10), status: 'active' },
    { id: 'sub_2', customer_id: 'cust_2', plan_id: 'plan_3', start_date: daysFromNow(-12), next_billing_date: daysFromNow(18), status: 'active' },
  ] as SubRow[],
  invoices: [
    {
      id: 'inv_1', number: 'INV-0001', subscription_id: 'sub_1', customer_id: 'cust_1',
      issue_date: daysFromNow(-20), due_date: daysFromNow(-6), subtotal: 1200, discount: 0, tax: 216,
      total: 1416, amount_paid: 1416, balance: 0, status: 'paid',
    },
  ] as InvoiceRow[],
  payments: [
    { id: 'pay_1', invoice_id: 'inv_1', amount: 1416, method: 'upi', status: 'succeeded', paid_at: daysFromNow(-19) },
  ] as PaymentRow[],
}

// ---------- helpers ----------
function find<T extends { id: ID }>(rows: T[], id: ID, label: string): T {
  const row = rows.find((r) => String(r.id) === String(id))
  if (!row) throw new ApiError(`${label} not found`, 404)
  return row
}
const customerName = (id: ID) => db.customers.find((c) => c.id === id)?.name ?? 'Unknown customer'

function hydratePlan(p: PlanRow): Plan {
  return { ...p, product_name: db.products.find((x) => x.id === p.product_id)?.name ?? 'Unknown product' }
}
function hydrateSub(s: SubRow): Subscription {
  const plan = find(db.plans, s.plan_id, 'Plan')
  return { ...s, customer_name: customerName(s.customer_id), plan_name: plan.name, price: plan.price, interval: plan.interval }
}
function hydrateInvoice(i: InvoiceRow): Invoice {
  return { ...i, customer_name: customerName(i.customer_id) }
}
function hydratePayment(p: PaymentRow): Payment {
  const inv = find(db.invoices, p.invoice_id, 'Invoice')
  return { ...p, invoice_number: inv.number, customer_name: customerName(inv.customer_id) }
}
const newestFirst = <T,>(rows: T[]) => [...rows].reverse()

function requireAuth() {
  if (!tokenStore.get()) throw new ApiError('Not authenticated', 401)
}
const demoUser: User = { id: 'user_1', email: 'admin@brightloop.com', name: 'Brightloop Admin' }

// ---------- the mock service ----------
export const mockApi: ApiService = {
  async login(email, password) {
    await delay(500)
    if (email.trim().toLowerCase() !== demoUser.email || password !== 'admin123') {
      throw new ApiError('Incorrect email or password.', 401)
    }
    const token = 'mock-token'
    tokenStore.set(token)
    return { token, user: clone(demoUser) }
  },
  async register(data) {
    await delay(500)
    const newUser: User = { id: `user_${Date.now()}`, name: data.name, email: data.email, role: data.role || 'staff' }
    const token = 'mock-token'
    tokenStore.set(token)
    return { token, user: newUser }
  },
  async me() {
    await delay(150)
    requireAuth()
    return clone(demoUser)
  },

  async dashboard() {
    await delay()
    requireAuth()
    const active = db.subscriptions.filter((s) => s.status === 'active')
    const mrr = active.reduce((sum, s) => {
      const plan = find(db.plans, s.plan_id, 'Plan')
      return sum + monthlyValue(plan.price, plan.interval)
    }, 0)
    const summary: DashboardSummary = {
      total_customers: db.customers.length,
      active_subscriptions: active.length,
      mrr: round2(mrr),
      total_invoices: db.invoices.length,
      outstanding_amount: round2(db.invoices.filter((i) => i.status !== 'void').reduce((sum, i) => sum + i.balance, 0)),
      recent_payments: newestFirst(db.payments).slice(0, 5).map(hydratePayment),
      recent_subscriptions: newestFirst(db.subscriptions).slice(0, 5).map(hydrateSub),
    }
    return clone(summary)
  },

  products: {
    async list() { await delay(); requireAuth(); return clone(newestFirst(db.products)) },
    async get(id) { await delay(150); requireAuth(); return clone(find(db.products, id, 'Product')) },
    async create(data) {
      await delay(); requireAuth()
      const product: Product = { ...data, id: nextId('prod'), variants: [], created_at: today() }
      db.products.push(product)
      return clone(product)
    },
    async update(id, data) {
      await delay(); requireAuth()
      const product = find(db.products, id, 'Product')
      Object.assign(product, data)
      return clone(product)
    },
    async remove(id) {
      // "Delete" = deactivate, so existing plans and invoices keep working.
      await delay(); requireAuth()
      find(db.products, id, 'Product').active = false
    },
    async addVariant(productId, data) {
      await delay(); requireAuth()
      const product = find(db.products, productId, 'Product')
      product.variants.push({ ...data, id: nextId('var') })
      return clone(product)
    },
    async updateVariant(productId, variantId, data) {
      await delay(); requireAuth()
      const product = find(db.products, productId, 'Product')
      Object.assign(find(product.variants, variantId, 'Variant'), data)
      return clone(product)
    },
    async removeVariant(productId, variantId) {
      await delay(); requireAuth()
      const product = find(db.products, productId, 'Product')
      find(product.variants, variantId, 'Variant')
      product.variants = product.variants.filter((v) => String(v.id) !== String(variantId))
      return clone(product)
    },
  },

  plans: {
    async list() { await delay(); requireAuth(); return newestFirst(db.plans).map(hydratePlan) },
    async get(id) { await delay(150); requireAuth(); return hydratePlan(find(db.plans, id, 'Plan')) },
    async create(data) {
      await delay(); requireAuth()
      find(db.products, data.product_id, 'Product')
      const plan: PlanRow = { ...data, id: nextId('plan') }
      db.plans.push(plan)
      return hydratePlan(plan)
    },
    async update(id, data) {
      await delay(); requireAuth()
      const plan = find(db.plans, id, 'Plan')
      Object.assign(plan, data)
      return hydratePlan(plan)
    },
    async setActive(id, active) {
      await delay(200); requireAuth()
      const plan = find(db.plans, id, 'Plan')
      plan.active = active
      return hydratePlan(plan)
    },
  },

  customers: {
    async list() { await delay(); requireAuth(); return clone(newestFirst(db.customers)) },
    async get(id) { await delay(150); requireAuth(); return clone(find(db.customers, id, 'Customer')) },
    async create(data) {
      await delay(); requireAuth()
      if (db.customers.some((c) => c.email.toLowerCase() === data.email.toLowerCase())) {
        throw new ApiError('A customer with this email already exists.', 409)
      }
      const customer: Customer = { ...data, id: nextId('cust'), created_at: today() }
      db.customers.push(customer)
      return clone(customer)
    },
    async update(id, data) {
      await delay(); requireAuth()
      const customer = find(db.customers, id, 'Customer')
      Object.assign(customer, data)
      return clone(customer)
    },
  },

  subscriptions: {
    async list() { await delay(); requireAuth(); return newestFirst(db.subscriptions).map(hydrateSub) },
    async get(id) { await delay(150); requireAuth(); return hydrateSub(find(db.subscriptions, id, 'Subscription')) },
    async create(data) {
      await delay(); requireAuth()
      find(db.customers, data.customer_id, 'Customer')
      const plan = find(db.plans, data.plan_id, 'Plan')
      if (!plan.active) throw new ApiError('This plan is inactive and cannot be subscribed to.', 400)
      const sub: SubRow = {
        id: nextId('sub'), customer_id: data.customer_id, plan_id: data.plan_id,
        start_date: data.start_date, next_billing_date: addInterval(data.start_date, plan.interval),
        status: 'active',
      }
      db.subscriptions.push(sub)
      return hydrateSub(sub)
    },
    async setStatus(id, status) {
      await delay(250); requireAuth()
      const sub = find(db.subscriptions, id, 'Subscription')
      if (sub.status === 'cancelled' || sub.status === 'expired') {
        throw new ApiError(`A ${sub.status} subscription cannot be changed.`, 400)
      }
      if (status === 'paused' && sub.status !== 'active') throw new ApiError('Only active subscriptions can be paused.', 400)
      if (status === 'active' && sub.status !== 'paused' && sub.status !== 'draft') {
        throw new ApiError('Only paused or draft subscriptions can be resumed.', 400)
      }
      sub.status = status
      return hydrateSub(sub)
    },
  },

  invoices: {
    async list() { await delay(); requireAuth(); return newestFirst(db.invoices).map(hydrateInvoice) },
    async get(id) { await delay(150); requireAuth(); return hydrateInvoice(find(db.invoices, id, 'Invoice')) },
    async generate(subscriptionId) {
      await delay(); requireAuth()
      const sub = find(db.subscriptions, subscriptionId, 'Subscription')
      const plan = find(db.plans, sub.plan_id, 'Plan')
      const subtotal = plan.price
      const discount = 0
      const tax = round2((subtotal - discount) * 0.18)
      const total = round2(subtotal - discount + tax)
      const invoice: InvoiceRow = {
        id: nextId('inv'), number: `INV-${String(db.invoices.length + 1).padStart(4, '0')}`,
        subscription_id: sub.id, customer_id: sub.customer_id, issue_date: today(), due_date: daysFromNow(14),
        subtotal, discount, tax, total, amount_paid: 0, balance: total, status: 'unpaid',
      }
      db.invoices.push(invoice)
      return hydrateInvoice(invoice)
    },
    async recordPayment(invoiceId, data) {
      await delay(); requireAuth()
      const invoice = find(db.invoices, invoiceId, 'Invoice')
      if (invoice.status === 'void') throw new ApiError('Cannot pay a void invoice.', 400)
      if (data.amount <= 0) throw new ApiError('Payment amount must be greater than zero.', 400)
      if (data.amount > invoice.balance + 0.001) throw new ApiError('Amount is more than the outstanding balance.', 400)
      invoice.amount_paid = round2(invoice.amount_paid + data.amount)
      invoice.balance = round2(invoice.total - invoice.amount_paid)
      invoice.status = invoice.balance <= 0 ? 'paid' : 'partial'
      db.payments.push({
        id: nextId('pay'), invoice_id: invoice.id, amount: data.amount, method: data.method,
        status: 'succeeded', paid_at: new Date().toISOString(),
      })
      return hydrateInvoice(invoice)
    },
  },

  payments: {
    async list() { await delay(); requireAuth(); return newestFirst(db.payments).map(hydratePayment) },
    async get(id) { await delay(150); requireAuth(); return hydratePayment(find(db.payments, id, 'Payment')) },
  },
}

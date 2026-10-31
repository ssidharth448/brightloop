import type { ApiService, Customer, DashboardSummary, Invoice, Payment, Plan, Product, Subscription, User } from '../types'
import { ApiError, request, tokenStore } from './http'

// ⚠️ Paths and payloads below are the PROPOSED contract from the brief.
// Compare with the backend's /docs page and adjust anything that differs.

const STATUS_ACTION = { active: 'resume', paused: 'pause', cancelled: 'cancel' } as const

export const realApi: ApiService = {
  async login(email, password) {
    // If the backend uses FastAPI's OAuth2PasswordRequestForm, switch to:
    //   request('/auth/login', { method: 'POST', form: { username: email, password } })
    const data = await request<{ access_token?: string; token?: string; user?: User }>('/auth/login', {
      method: 'POST',
      body: { email, password },
    })
    const token = data.access_token ?? data.token
    if (!token) throw new ApiError('Login response did not include a token.', 500)
    tokenStore.set(token)
    const user = data.user ?? (await request<User>('/auth/me'))
    return { token, user }
  },
  me: () => request<User>('/auth/me'),
  dashboard: () => request<DashboardSummary>('/dashboard/summary'),

  products: {
    list: () => request<Product[]>('/products'),
    get: (id) => request<Product>(`/products/${id}`),
    create: (data) => request<Product>('/products', { method: 'POST', body: data }),
    update: (id, data) => request<Product>(`/products/${id}`, { method: 'PUT', body: data }),
    remove: (id) => request<void>(`/products/${id}`, { method: 'DELETE' }),
    addVariant: async (productId, data) => {
      await request(`/products/${productId}/variants`, { method: 'POST', body: data })
      return request<Product>(`/products/${productId}`)
    },
    updateVariant: async (productId, variantId, data) => {
      await request(`/products/${productId}/variants/${variantId}`, { method: 'PUT', body: data })
      return request<Product>(`/products/${productId}`)
    },
    removeVariant: async (productId, variantId) => {
      await request(`/products/${productId}/variants/${variantId}`, { method: 'DELETE' })
      return request<Product>(`/products/${productId}`)
    },
  },

  plans: {
    list: () => request<Plan[]>('/plans'),
    get: (id) => request<Plan>(`/plans/${id}`),
    create: (data) => request<Plan>('/plans', { method: 'POST', body: data }),
    update: (id, data) => request<Plan>(`/plans/${id}`, { method: 'PUT', body: data }),
    setActive: (id, active) => request<Plan>(`/plans/${id}`, { method: 'PATCH', body: { active } }),
  },

  customers: {
    list: () => request<Customer[]>('/customers'),
    get: (id) => request<Customer>(`/customers/${id}`),
    create: (data) => request<Customer>('/customers', { method: 'POST', body: data }),
    update: (id, data) => request<Customer>(`/customers/${id}`, { method: 'PUT', body: data }),
  },

  subscriptions: {
    list: () => request<Subscription[]>('/subscriptions'),
    get: (id) => request<Subscription>(`/subscriptions/${id}`),
    create: (data) => request<Subscription>('/subscriptions', { method: 'POST', body: data }),
    setStatus: (id, status) =>
      request<Subscription>(`/subscriptions/${id}/${STATUS_ACTION[status]}`, { method: 'POST' }),
  },

  invoices: {
    list: () => request<Invoice[]>('/invoices'),
    get: (id) => request<Invoice>(`/invoices/${id}`),
    generate: (subscriptionId) =>
      request<Invoice>('/invoices', { method: 'POST', body: { subscription_id: subscriptionId } }),
    recordPayment: async (invoiceId, data) => {
      await request(`/invoices/${invoiceId}/payments`, { method: 'POST', body: data })
      return request<Invoice>(`/invoices/${invoiceId}`)
    },
  },

  payments: {
    list: () => request<Payment[]>('/payments'),
    get: (id) => request<Payment>(`/payments/${id}`),
  },
}

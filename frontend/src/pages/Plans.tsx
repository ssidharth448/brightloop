import { useMemo, useState, type FormEvent } from 'react'
import { Check, Edit2, Layers, Plus } from 'lucide-react'
import { StatusBadge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { EmptyState } from '../components/ui/EmptyState'
import { ErrorState } from '../components/ui/ErrorState'
import { Input } from '../components/ui/Input'
import { Modal } from '../components/ui/Modal'
import { PageHeader } from '../components/ui/PageHeader'
import { SearchBar } from '../components/ui/SearchBar'
import { Select } from '../components/ui/Select'
import { PageLoader } from '../components/ui/Spinner'
import { useFetch } from '../hooks/useFetch'
import { useToast } from '../hooks/useToast'
import { formatCurrency, intervalLabel } from '../lib/format'
import { api } from '../services/api'
import type { BillingInterval, Plan, PlanInput } from '../types'

export default function Plans() {
  const { data: plans, loading, error, reload } = useFetch(api.plans.list)
  const { data: products } = useFetch(api.products.list)
  const toast = useToast()

  const [search, setSearch] = useState('')
  const [intervalFilter, setIntervalFilter] = useState<string>('all')
  const [modalOpen, setModalOpen] = useState(false)
  const [editingPlan, setEditingPlan] = useState<Plan | null>(null)
  const [submitting, setSubmitting] = useState(false)

  // Form fields
  const [name, setName] = useState('')
  const [productId, setProductId] = useState<string>('')
  const [price, setPrice] = useState('')
  const [interval, setInterval] = useState<BillingInterval>('monthly')
  const [active, setActive] = useState(true)
  const [formErrors, setFormErrors] = useState<{ name?: string; productId?: string; price?: string }>({})

  const filteredPlans = useMemo(() => {
    if (!plans) return []
    const q = search.trim().toLowerCase()
    return plans.filter((p) => {
      const matchesSearch =
        !q ||
        p.name.toLowerCase().includes(q) ||
        (p.product_name && p.product_name.toLowerCase().includes(q))
      const matchesInterval = intervalFilter === 'all' || p.interval === intervalFilter
      return matchesSearch && matchesInterval
    })
  }, [plans, search, intervalFilter])

  function openCreateModal() {
    setEditingPlan(null)
    setName('')
    setProductId(products && products.length > 0 ? String(products[0].id) : '')
    setPrice('')
    setInterval('monthly')
    setActive(true)
    setFormErrors({})
    setModalOpen(true)
  }

  function openEditModal(plan: Plan) {
    setEditingPlan(plan)
    setName(plan.name)
    setProductId(String(plan.product_id))
    setPrice(String(plan.price))
    setInterval(plan.interval)
    setActive(plan.active)
    setFormErrors({})
    setModalOpen(true)
  }

  async function handleToggleActive(plan: Plan) {
    try {
      await api.plans.setActive(plan.id, !plan.active)
      toast.success(`${plan.name} is now ${!plan.active ? 'active' : 'inactive'}`)
      reload()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to update plan status.')
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const errors: typeof formErrors = {}
    if (!name.trim()) errors.name = 'Plan name is required.'
    if (!productId) errors.productId = 'Please select a product.'
    const priceNum = parseFloat(price)
    if (isNaN(priceNum) || priceNum < 0) errors.price = 'Enter a valid non-negative price.'
    setFormErrors(errors)
    if (Object.keys(errors).length) return

    setSubmitting(true)
    try {
      const payload: PlanInput = {
        name: name.trim(),
        product_id: productId,
        price: priceNum,
        interval,
        active,
      }
      if (editingPlan) {
        await api.plans.update(editingPlan.id, payload)
        toast.success(`Updated ${payload.name}`)
      } else {
        await api.plans.create(payload)
        toast.success(`Created plan ${payload.name}`)
      }
      setModalOpen(false)
      reload()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to save plan.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <PageHeader
        title="Plans"
        description="Define billing tiers, prices, and frequencies for your products."
        actions={
          <Button onClick={openCreateModal}>
            <Plus className="size-4" />
            New Plan
          </Button>
        }
      />

      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <SearchBar value={search} onChange={setSearch} placeholder="Search plans or products…" />
        <div className="flex items-center gap-2">
          <Select
            value={intervalFilter}
            onChange={(e) => setIntervalFilter(e.target.value)}
            className="w-40"
          >
            <option value="all">All Intervals</option>
            <option value="monthly">Monthly</option>
            <option value="quarterly">Quarterly</option>
            <option value="yearly">Yearly</option>
          </Select>
        </div>
      </div>

      {loading && <PageLoader />}
      {error && <ErrorState message={error} onRetry={reload} />}

      {!loading && !error && filteredPlans.length === 0 && (
        <EmptyState
          icon={Layers}
          title={search ? 'No matching plans' : 'No plans yet'}
          description={
            search
              ? 'Try modifying your search or interval filter.'
              : 'Create a plan to specify how much customers pay and on what schedule.'
          }
          action={
            !search && (
              <Button onClick={openCreateModal}>
                <Plus className="size-4" />
                Add Plan
              </Button>
            )
          }
        />
      )}

      {!loading && !error && filteredPlans.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filteredPlans.map((plan) => (
            <div
              key={plan.id}
              className="flex flex-col justify-between rounded-xl border border-gray-200 bg-white p-5 shadow-xs transition-shadow hover:shadow-sm"
            >
              <div>
                <div className="flex items-start justify-between gap-2">
                  <span className="text-xs font-semibold uppercase tracking-wider text-brand-700">
                    {plan.product_name || 'Product'}
                  </span>
                  <StatusBadge status={plan.active ? 'active' : 'inactive'} />
                </div>
                <h3 className="mt-1 text-lg font-semibold text-gray-900">{plan.name}</h3>

                <div className="mt-4 flex items-baseline gap-1.5">
                  <span className="text-3xl font-bold tracking-tight text-gray-900">
                    {formatCurrency(plan.price)}
                  </span>
                  <span className="text-sm font-medium text-gray-500">
                    / {intervalLabel[plan.interval] || plan.interval}
                  </span>
                </div>
              </div>

              <div className="mt-6 flex items-center justify-between border-t border-gray-100 pt-3 text-xs">
                <button
                  type="button"
                  onClick={() => handleToggleActive(plan)}
                  className={`inline-flex items-center gap-1 font-medium transition-colors ${
                    plan.active
                      ? 'text-gray-500 hover:text-amber-700'
                      : 'text-brand-700 hover:text-brand-900'
                  }`}
                >
                  <Check className={`size-3.5 ${plan.active ? 'text-brand-700' : 'text-gray-400'}`} />
                  {plan.active ? 'Deactivate' : 'Activate'}
                </button>
                <Button variant="ghost" size="sm" onClick={() => openEditModal(plan)}>
                  <Edit2 className="size-3.5" />
                  Edit
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Plan Create/Edit Modal */}
      <Modal
        open={modalOpen}
        title={editingPlan ? `Edit ${editingPlan.name}` : 'New Plan'}
        onClose={() => setModalOpen(false)}
        footer={
          <>
            <Button variant="secondary" onClick={() => setModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSubmit} loading={submitting}>
              {editingPlan ? 'Save Changes' : 'Create Plan'}
            </Button>
          </>
        }
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Plan Name"
            placeholder="e.g. Standard Monthly"
            value={name}
            onChange={(e) => setName(e.target.value)}
            error={formErrors.name}
            required
          />

          <Select
            label="Product"
            value={productId}
            onChange={(e) => setProductId(e.target.value)}
            error={formErrors.productId}
            required
          >
            <option value="">Select a product…</option>
            {products?.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} ({formatCurrency(p.base_price)})
              </option>
            ))}
          </Select>

          <Input
            label="Price (INR)"
            type="number"
            step="0.01"
            min="0"
            placeholder="1200.00"
            value={price}
            onChange={(e) => setPrice(e.target.value)}
            error={formErrors.price}
            required
          />

          <Select
            label="Billing Interval"
            value={interval}
            onChange={(e) => setInterval(e.target.value as BillingInterval)}
          >
            <option value="monthly">Monthly</option>
            <option value="quarterly">Quarterly</option>
            <option value="yearly">Yearly</option>
          </Select>

          <label className="flex items-center gap-2 pt-1 text-sm font-medium text-gray-800">
            <input
              type="checkbox"
              checked={active}
              onChange={(e) => setActive(e.target.checked)}
              className="size-4 rounded border-gray-300 text-brand-800 focus:ring-brand-700"
            />
            Plan is Active for new subscriptions
          </label>
        </form>
      </Modal>
    </>
  )
}

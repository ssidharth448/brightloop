import { useMemo, useState, type FormEvent } from 'react'
import { FilePlus2, Pause, Play, Plus, Repeat, XCircle } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { StatusBadge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { ConfirmDialog } from '../components/ui/ConfirmDialog'
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
import { formatCurrency, formatDate, intervalLabel } from '../lib/format'
import { api } from '../services/api'
import type { Subscription, SubscriptionInput } from '../types'

const todayIso = () => new Date().toISOString().slice(0, 10)

export default function Subscriptions() {
  const { data: subscriptions, loading, error, reload } = useFetch(api.subscriptions.list)
  const { data: customers } = useFetch(api.customers.list)
  const { data: plans } = useFetch(api.plans.list)
  const toast = useToast()
  const navigate = useNavigate()

  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [modalOpen, setModalOpen] = useState(false)
  const [cancelTarget, setCancelTarget] = useState<Subscription | null>(null)
  const [generatingForSub, setGeneratingForSub] = useState<Subscription | null>(null)
  const [submitting, setSubmitting] = useState(false)

  // Form fields
  const [customerId, setCustomerId] = useState('')
  const [planId, setPlanId] = useState('')
  const [startDate, setStartDate] = useState(todayIso())
  const [formErrors, setFormErrors] = useState<{ customerId?: string; planId?: string }>({})

  const filteredSubs = useMemo(() => {
    if (!subscriptions) return []
    const q = search.trim().toLowerCase()
    return subscriptions.filter((s) => {
      const matchesSearch =
        !q ||
        (s.customer_name && s.customer_name.toLowerCase().includes(q)) ||
        (s.plan_name && s.plan_name.toLowerCase().includes(q))
      const matchesStatus = statusFilter === 'all' || s.status === statusFilter
      return matchesSearch && matchesStatus
    })
  }, [subscriptions, search, statusFilter])

  function openCreateModal() {
    setCustomerId(customers && customers.length > 0 ? String(customers[0].id) : '')
    setPlanId(plans && plans.length > 0 ? String(plans[0].id) : '')
    setStartDate(todayIso())
    setFormErrors({})
    setModalOpen(true)
  }

  async function handleStatusChange(sub: Subscription, nextStatus: 'active' | 'paused' | 'cancelled') {
    setSubmitting(true)
    try {
      await api.subscriptions.setStatus(sub.id, nextStatus)
      toast.success(`Subscription marked as ${nextStatus}`)
      reload()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : `Failed to update status to ${nextStatus}`)
    } finally {
      setSubmitting(false)
    }
  }

  async function handleGenerateInvoice(sub: Subscription) {
    setGeneratingForSub(sub)
    try {
      const invoice = await api.invoices.generate(sub.id)
      toast.success(`Generated invoice ${invoice.number || invoice.id} for ${sub.customer_name}`)
      navigate('/invoices')
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to generate invoice.')
    } finally {
      setGeneratingForSub(null)
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const errors: typeof formErrors = {}
    if (!customerId) errors.customerId = 'Please select a customer.'
    if (!planId) errors.planId = 'Please select a plan.'
    setFormErrors(errors)
    if (Object.keys(errors).length) return

    setSubmitting(true)
    try {
      const payload: SubscriptionInput = {
        customer_id: customerId,
        plan_id: planId,
        start_date: startDate,
      }
      await api.subscriptions.create(payload)
      toast.success('Subscription created successfully')
      setModalOpen(false)
      reload()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to create subscription.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <PageHeader
        title="Subscriptions"
        description="Active recurring customer subscriptions and automated renewal schedules."
        actions={
          <Button onClick={openCreateModal}>
            <Plus className="size-4" />
            New Subscription
          </Button>
        }
      />

      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <SearchBar value={search} onChange={setSearch} placeholder="Search by customer or plan…" />
        <Select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="w-40"
        >
          <option value="all">All Statuses</option>
          <option value="active">Active</option>
          <option value="paused">Paused</option>
          <option value="cancelled">Cancelled</option>
        </Select>
      </div>

      {loading && <PageLoader />}
      {error && <ErrorState message={error} onRetry={reload} />}

      {!loading && !error && filteredSubs.length === 0 && (
        <EmptyState
          icon={Repeat}
          title={search ? 'No matching subscriptions' : 'No subscriptions yet'}
          description={
            search
              ? 'Try adjusting your search or status filter.'
              : 'Subscribe your first customer to an active plan.'
          }
          action={
            !search && (
              <Button onClick={openCreateModal}>
                <Plus className="size-4" />
                Add Subscription
              </Button>
            )
          }
        />
      )}

      {!loading && !error && filteredSubs.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-gray-700">
              <thead className="border-b border-gray-200 bg-gray-50 text-xs font-medium text-gray-500 uppercase tracking-wider">
                <tr>
                  <th scope="col" className="px-6 py-3.5">Customer</th>
                  <th scope="col" className="px-6 py-3.5">Plan & Rate</th>
                  <th scope="col" className="px-6 py-3.5">Billing Period</th>
                  <th scope="col" className="px-6 py-3.5">Next Renewal</th>
                  <th scope="col" className="px-6 py-3.5">Status</th>
                  <th scope="col" className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filteredSubs.map((s) => (
                  <tr key={s.id} className="hover:bg-gray-50/80 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap font-medium text-gray-900">
                      <div>{s.customer_name || `Customer #${s.customer_id}`}</div>
                      <div className="text-xs text-gray-400">Sub #{s.id}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="font-medium text-gray-900">{s.plan_name || `Plan #${s.plan_id}`}</div>
                      <div className="text-xs text-gray-500">
                        {formatCurrency(s.price)} / {intervalLabel[s.interval] || s.interval}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-xs text-gray-500">
                      Started {formatDate(s.start_date)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-xs">
                      {s.next_billing_date ? (
                        <span className="font-medium text-gray-800">{formatDate(s.next_billing_date)}</span>
                      ) : (
                        <span className="text-gray-400">—</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <StatusBadge status={s.status} />
                    </td>
                    <td className="px-6 py-4 text-right whitespace-nowrap">
                      <div className="flex items-center justify-end gap-1.5">
                        {s.status === 'active' && (
                          <>
                            <Button
                              variant="ghost"
                              size="sm"
                              title="Generate Invoice"
                              onClick={() => handleGenerateInvoice(s)}
                              loading={generatingForSub?.id === s.id}
                            >
                              <FilePlus2 className="size-3.5 text-brand-700" />
                              <span className="hidden sm:inline">Bill</span>
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              title="Pause Subscription"
                              onClick={() => handleStatusChange(s, 'paused')}
                            >
                              <Pause className="size-3.5 text-amber-600" />
                              <span className="hidden sm:inline">Pause</span>
                            </Button>
                          </>
                        )}

                        {s.status === 'paused' && (
                          <Button
                            variant="ghost"
                            size="sm"
                            title="Resume Subscription"
                            onClick={() => handleStatusChange(s, 'active')}
                          >
                            <Play className="size-3.5 text-brand-700" />
                            <span className="hidden sm:inline">Resume</span>
                          </Button>
                        )}

                        {(s.status === 'active' || s.status === 'paused') && (
                          <Button
                            variant="ghost"
                            size="sm"
                            title="Cancel Subscription"
                            className="text-red-600 hover:bg-red-50 hover:text-red-700"
                            onClick={() => setCancelTarget(s)}
                          >
                            <XCircle className="size-3.5" />
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Subscription Create Modal */}
      <Modal
        open={modalOpen}
        title="New Subscription"
        onClose={() => setModalOpen(false)}
        footer={
          <>
            <Button variant="secondary" onClick={() => setModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSubmit} loading={submitting}>
              Start Subscription
            </Button>
          </>
        }
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <Select
            label="Customer"
            value={customerId}
            onChange={(e) => setCustomerId(e.target.value)}
            error={formErrors.customerId}
            required
          >
            <option value="">Select a customer…</option>
            {customers?.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name} {c.company ? `(${c.company})` : ''} — {c.email}
              </option>
            ))}
          </Select>

          <Select
            label="Plan"
            value={planId}
            onChange={(e) => setPlanId(e.target.value)}
            error={formErrors.planId}
            required
          >
            <option value="">Select a plan…</option>
            {plans?.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} ({p.product_name}) — {formatCurrency(p.price)} / {p.interval}
              </option>
            ))}
          </Select>

          <Input
            label="Start Date"
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            required
          />
        </form>
      </Modal>

      {/* Cancel Confirmation Dialog */}
      <ConfirmDialog
        open={Boolean(cancelTarget)}
        title="Cancel Subscription"
        message={`Are you sure you want to cancel the subscription for ${cancelTarget?.customer_name}? Future billing will cease.`}
        confirmLabel="Cancel Subscription"
        danger
        loading={submitting}
        onConfirm={async () => {
          if (cancelTarget) {
            await handleStatusChange(cancelTarget, 'cancelled')
            setCancelTarget(null)
          }
        }}
        onCancel={() => setCancelTarget(null)}
      />
    </>
  )
}

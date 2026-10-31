import { useMemo, useState, type FormEvent } from 'react'
import { CreditCard, Eye, FilePlus2, FileText } from 'lucide-react'
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
import { formatCurrency, formatDate } from '../lib/format'
import { api } from '../services/api'
import type { Invoice, PaymentMethod } from '../types'

export default function Invoices() {
  const { data: invoices, loading, error, reload } = useFetch(api.invoices.list)
  const { data: subscriptions } = useFetch(api.subscriptions.list)
  const toast = useToast()

  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')

  // Generate Modal
  const [generateModalOpen, setGenerateModalOpen] = useState(false)
  const [selectedSubId, setSelectedSubId] = useState('')

  // View Details Modal
  const [viewInvoice, setViewInvoice] = useState<Invoice | null>(null)

  // Record Payment Modal
  const [paymentInvoice, setPaymentInvoice] = useState<Invoice | null>(null)
  const [payAmount, setPayAmount] = useState('')
  const [payMethod, setPayMethod] = useState<PaymentMethod>('card')
  const [payError, setPayError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const filteredInvoices = useMemo(() => {
    if (!invoices) return []
    const q = search.trim().toLowerCase()
    return invoices.filter((inv) => {
      const matchesSearch =
        !q ||
        (inv.number && inv.number.toLowerCase().includes(q)) ||
        (inv.customer_name && inv.customer_name.toLowerCase().includes(q))
      const matchesStatus = statusFilter === 'all' || inv.status === statusFilter
      return matchesSearch && matchesStatus
    })
  }, [invoices, search, statusFilter])

  function openGenerateModal() {
    setSelectedSubId(subscriptions && subscriptions.length > 0 ? String(subscriptions[0].id) : '')
    setGenerateModalOpen(true)
  }

  function openPaymentModal(inv: Invoice) {
    setPaymentInvoice(inv)
    setPayAmount(String(inv.balance > 0 ? inv.balance : inv.total))
    setPayMethod('card')
    setPayError(null)
  }

  async function handleGenerateSubmit(e: FormEvent) {
    e.preventDefault()
    if (!selectedSubId) return
    setSubmitting(true)
    try {
      const created = await api.invoices.generate(selectedSubId)
      toast.success(`Generated invoice ${created.number || created.id}`)
      setGenerateModalOpen(false)
      reload()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to generate invoice.')
    } finally {
      setSubmitting(false)
    }
  }

  async function handlePaymentSubmit(e: FormEvent) {
    e.preventDefault()
    if (!paymentInvoice) return
    const amt = parseFloat(payAmount)
    if (isNaN(amt) || amt <= 0) {
      setPayError('Enter a valid payment amount.')
      return
    }
    if (amt > paymentInvoice.balance) {
      setPayError(`Payment cannot exceed outstanding balance (${formatCurrency(paymentInvoice.balance)}).`)
      return
    }

    setSubmitting(true)
    try {
      await api.invoices.recordPayment(paymentInvoice.id, {
        amount: amt,
        method: payMethod,
      })
      toast.success(`Recorded payment of ${formatCurrency(amt)} for ${paymentInvoice.number}`)
      setPaymentInvoice(null)
      reload()
    } catch (err) {
      setPayError(err instanceof Error ? err.message : 'Failed to record payment.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <PageHeader
        title="Invoices"
        description="Review billing statements, outstanding balances, and collect payments."
        actions={
          <Button onClick={openGenerateModal}>
            <FilePlus2 className="size-4" />
            Generate Invoice
          </Button>
        }
      />

      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <SearchBar value={search} onChange={setSearch} placeholder="Search invoice # or customer…" />
        <Select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="w-40"
        >
          <option value="all">All Statuses</option>
          <option value="unpaid">Unpaid</option>
          <option value="partial">Partial</option>
          <option value="paid">Paid</option>
        </Select>
      </div>

      {loading && <PageLoader />}
      {error && <ErrorState message={error} onRetry={reload} />}

      {!loading && !error && filteredInvoices.length === 0 && (
        <EmptyState
          icon={FileText}
          title={search ? 'No matching invoices' : 'No invoices yet'}
          description={
            search
              ? 'Try modifying your search or status filter.'
              : 'Generate an invoice from an active subscription to start billing.'
          }
          action={
            !search && (
              <Button onClick={openGenerateModal}>
                <FilePlus2 className="size-4" />
                Generate Invoice
              </Button>
            )
          }
        />
      )}

      {!loading && !error && filteredInvoices.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-gray-700">
              <thead className="border-b border-gray-200 bg-gray-50 text-xs font-medium text-gray-500 uppercase tracking-wider">
                <tr>
                  <th scope="col" className="px-6 py-3.5">Invoice #</th>
                  <th scope="col" className="px-6 py-3.5">Customer</th>
                  <th scope="col" className="px-6 py-3.5">Issue / Due Date</th>
                  <th scope="col" className="px-6 py-3.5">Total Amount</th>
                  <th scope="col" className="px-6 py-3.5">Balance Owed</th>
                  <th scope="col" className="px-6 py-3.5">Status</th>
                  <th scope="col" className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filteredInvoices.map((inv) => (
                  <tr key={inv.id} className="hover:bg-gray-50/80 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap font-semibold text-gray-900">
                      {inv.number || `INV-${inv.id}`}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="font-medium text-gray-900">{inv.customer_name || 'Customer'}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-xs text-gray-500">
                      <div>Issued: {formatDate(inv.issue_date)}</div>
                      <div className="text-gray-400">Due: {formatDate(inv.due_date)}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="font-semibold text-gray-900">{formatCurrency(inv.total)}</span>
                      {inv.tax > 0 && (
                        <div className="text-xs text-gray-400">incl. {formatCurrency(inv.tax)} tax</div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {inv.balance > 0 ? (
                        <span className="font-medium text-amber-700">{formatCurrency(inv.balance)}</span>
                      ) : (
                        <span className="text-brand-700 font-medium">Paid in full</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <StatusBadge status={inv.status} />
                    </td>
                    <td className="px-6 py-4 text-right whitespace-nowrap">
                      <div className="flex items-center justify-end gap-1.5">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setViewInvoice(inv)}
                          title="View Invoice Details"
                        >
                          <Eye className="size-3.5" />
                        </Button>
                        {inv.balance > 0 && (
                          <Button
                            variant="primary"
                            size="sm"
                            onClick={() => openPaymentModal(inv)}
                          >
                            <CreditCard className="size-3.5" />
                            Record Pay
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

      {/* Generate Invoice Modal */}
      <Modal
        open={generateModalOpen}
        title="Generate Invoice from Subscription"
        onClose={() => setGenerateModalOpen(false)}
        footer={
          <>
            <Button variant="secondary" onClick={() => setGenerateModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleGenerateSubmit} loading={submitting}>
              Generate
            </Button>
          </>
        }
      >
        <form onSubmit={handleGenerateSubmit} className="space-y-4">
          <Select
            label="Active Subscription"
            value={selectedSubId}
            onChange={(e) => setSelectedSubId(e.target.value)}
            required
          >
            <option value="">Select a subscription…</option>
            {subscriptions
              ?.filter((s) => s.status === 'active' || s.status === 'paused')
              .map((s) => (
                <option key={s.id} value={s.id}>
                  #{s.id} — {s.customer_name} ({s.plan_name} — {formatCurrency(s.price)})
                </option>
              ))}
          </Select>
          <p className="text-xs text-gray-500">
            Generating an invoice will automatically calculate taxes, subtotal, and set a 30-day payment due date.
          </p>
        </form>
      </Modal>

      {/* Record Payment Modal */}
      <Modal
        open={Boolean(paymentInvoice)}
        title={`Record Payment for ${paymentInvoice?.number || ''}`}
        onClose={() => setPaymentInvoice(null)}
        footer={
          <>
            <Button variant="secondary" onClick={() => setPaymentInvoice(null)}>
              Cancel
            </Button>
            <Button onClick={handlePaymentSubmit} loading={submitting}>
              Confirm Payment
            </Button>
          </>
        }
      >
        <form onSubmit={handlePaymentSubmit} className="space-y-4">
          {payError && (
            <div className="rounded-md bg-red-50 p-2.5 text-xs text-red-700">
              {payError}
            </div>
          )}

          <div className="rounded-lg bg-gray-50 p-3 text-sm">
            <div className="flex justify-between text-gray-500">
              <span>Customer:</span>
              <span className="font-medium text-gray-800">{paymentInvoice?.customer_name}</span>
            </div>
            <div className="flex justify-between text-gray-500 mt-1">
              <span>Invoice Total:</span>
              <span>{paymentInvoice ? formatCurrency(paymentInvoice.total) : '0'}</span>
            </div>
            <div className="flex justify-between font-medium text-gray-900 mt-1 border-t border-gray-200 pt-1">
              <span>Outstanding Balance:</span>
              <span className="text-amber-700">{paymentInvoice ? formatCurrency(paymentInvoice.balance) : '0'}</span>
            </div>
          </div>

          <Input
            label="Payment Amount (INR)"
            type="number"
            step="0.01"
            min="0.01"
            max={paymentInvoice?.balance}
            value={payAmount}
            onChange={(e) => setPayAmount(e.target.value)}
            required
          />

          <Select
            label="Payment Method"
            value={payMethod}
            onChange={(e) => setPayMethod(e.target.value as PaymentMethod)}
          >
            <option value="card">Credit / Debit Card</option>
            <option value="upi">UPI / QR Code</option>
            <option value="bank_transfer">Net Banking / NEFT</option>
            <option value="cash">Cash / Cheque</option>
          </Select>
        </form>
      </Modal>

      {/* View Invoice Details Modal */}
      <Modal
        open={Boolean(viewInvoice)}
        title={`Invoice ${viewInvoice?.number || ''}`}
        onClose={() => setViewInvoice(null)}
        size="md"
        footer={
          <Button variant="secondary" onClick={() => setViewInvoice(null)}>
            Close
          </Button>
        }
      >
        {viewInvoice && (
          <div className="space-y-4 text-sm">
            <div className="flex items-center justify-between border-b border-gray-100 pb-3">
              <div>
                <div className="font-semibold text-gray-900">{viewInvoice.customer_name}</div>
                <div className="text-xs text-gray-500">Issued: {formatDate(viewInvoice.issue_date)}</div>
                <div className="text-xs text-gray-500">Due: {formatDate(viewInvoice.due_date)}</div>
              </div>
              <StatusBadge status={viewInvoice.status} />
            </div>

            <div className="rounded-lg border border-gray-100 bg-gray-50 p-4 space-y-2">
              <div className="flex justify-between text-gray-600">
                <span>Subtotal</span>
                <span>{formatCurrency(viewInvoice.subtotal)}</span>
              </div>
              {viewInvoice.discount > 0 && (
                <div className="flex justify-between text-brand-700">
                  <span>Discount</span>
                  <span>-{formatCurrency(viewInvoice.discount)}</span>
                </div>
              )}
              <div className="flex justify-between text-gray-600">
                <span>Tax</span>
                <span>+{formatCurrency(viewInvoice.tax)}</span>
              </div>
              <div className="flex justify-between font-bold text-gray-900 border-t border-gray-200 pt-2 text-base">
                <span>Total</span>
                <span>{formatCurrency(viewInvoice.total)}</span>
              </div>
              <div className="flex justify-between text-brand-800 text-xs">
                <span>Amount Paid</span>
                <span>{formatCurrency(viewInvoice.amount_paid)}</span>
              </div>
              <div className="flex justify-between font-semibold text-amber-800 text-sm">
                <span>Remaining Balance</span>
                <span>{formatCurrency(viewInvoice.balance)}</span>
              </div>
            </div>
          </div>
        )}
      </Modal>
    </>
  )
}

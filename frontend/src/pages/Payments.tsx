import { useMemo, useState } from 'react'
import { CreditCard } from 'lucide-react'
import { StatusBadge } from '../components/ui/Badge'
import { EmptyState } from '../components/ui/EmptyState'
import { ErrorState } from '../components/ui/ErrorState'
import { PageHeader } from '../components/ui/PageHeader'
import { SearchBar } from '../components/ui/SearchBar'
import { Select } from '../components/ui/Select'
import { PageLoader } from '../components/ui/Spinner'
import { useFetch } from '../hooks/useFetch'
import { formatCurrency, formatDate, titleCase } from '../lib/format'
import { api } from '../services/api'

export default function Payments() {
  const { data: payments, loading, error, reload } = useFetch(api.payments.list)

  const [search, setSearch] = useState('')
  const [methodFilter, setMethodFilter] = useState<string>('all')

  const filteredPayments = useMemo(() => {
    if (!payments) return []
    const q = search.trim().toLowerCase()
    return payments.filter((p) => {
      const matchesSearch =
        !q ||
        (p.invoice_number && p.invoice_number.toLowerCase().includes(q)) ||
        (p.customer_name && p.customer_name.toLowerCase().includes(q))
      const matchesMethod = methodFilter === 'all' || p.method === methodFilter
      return matchesSearch && matchesMethod
    })
  }, [payments, search, methodFilter])

  return (
    <>
      <PageHeader
        title="Payments"
        description="Historical log of all payment transactions settled against invoices."
      />

      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <SearchBar value={search} onChange={setSearch} placeholder="Search invoice # or customer…" />
        <Select
          value={methodFilter}
          onChange={(e) => setMethodFilter(e.target.value)}
          className="w-40"
        >
          <option value="all">All Methods</option>
          <option value="card">Card</option>
          <option value="upi">UPI</option>
          <option value="bank_transfer">Net Banking</option>
          <option value="cash">Cash</option>
        </Select>
      </div>

      {loading && <PageLoader />}
      {error && <ErrorState message={error} onRetry={reload} />}

      {!loading && !error && filteredPayments.length === 0 && (
        <EmptyState
          icon={CreditCard}
          title={search ? 'No matching payments' : 'No payments yet'}
          description={
            search
              ? 'Try modifying your search query or payment method filter.'
              : 'Payments will appear here when recorded against invoices.'
          }
        />
      )}

      {!loading && !error && filteredPayments.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-gray-700">
              <thead className="border-b border-gray-200 bg-gray-50 text-xs font-medium text-gray-500 uppercase tracking-wider">
                <tr>
                  <th scope="col" className="px-6 py-3.5">Payment ID</th>
                  <th scope="col" className="px-6 py-3.5">Invoice #</th>
                  <th scope="col" className="px-6 py-3.5">Customer</th>
                  <th scope="col" className="px-6 py-3.5">Amount</th>
                  <th scope="col" className="px-6 py-3.5">Method</th>
                  <th scope="col" className="px-6 py-3.5">Status</th>
                  <th scope="col" className="px-6 py-3.5">Date Paid</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filteredPayments.map((p) => (
                  <tr key={p.id} className="hover:bg-gray-50/80 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap text-xs font-mono text-gray-500">
                      PAY-{p.id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap font-medium text-gray-900">
                      {p.invoice_number || `INV-${p.invoice_id}`}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-800">
                      {p.customer_name || 'Customer'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap font-semibold text-brand-900">
                      {formatCurrency(p.amount)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="inline-flex items-center rounded-md bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-700 uppercase">
                        {titleCase(p.method || 'Unknown')}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <StatusBadge status={p.status} />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-xs text-gray-500">
                      {p.paid_at ? formatDate(p.paid_at) : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  )
}

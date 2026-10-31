import { ArrowRight, CreditCard, FileText, IndianRupee, Plus, Repeat, TrendingUp, Users } from 'lucide-react'
import { Link } from 'react-router-dom'
import { StatCard } from '../components/dashboard/StatCard'
import { StatusBadge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { ErrorState } from '../components/ui/ErrorState'
import { PageHeader } from '../components/ui/PageHeader'
import { PageLoader } from '../components/ui/Spinner'
import { useFetch } from '../hooks/useFetch'
import { formatCurrency, formatDate, titleCase } from '../lib/format'
import { api } from '../services/api'

export default function Dashboard() {
  const { data, loading, error, reload } = useFetch(api.dashboard)

  return (
    <>
      <PageHeader
        title="Dashboard"
        description="Real-time pulse of your subscription recurring revenue and operations."
        actions={
          <div className="flex items-center gap-2">
            <Link to="/subscriptions">
              <Button size="sm">
                <Plus className="size-4" />
                New Subscription
              </Button>
            </Link>
          </div>
        }
      />

      {loading && <PageLoader />}
      {error && <ErrorState message={error} onRetry={reload} />}

      {data && (
        <div className="space-y-8">
          {/* Top Metric Cards */}
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
            <StatCard label="Total Customers" value={String(data.total_customers)} icon={Users} />
            <StatCard label="Active Subscriptions" value={String(data.active_subscriptions)} icon={Repeat} />
            <StatCard label="Monthly Recurring Revenue" value={formatCurrency(data.mrr)} icon={TrendingUp} />
            <StatCard label="Total Invoices" value={String(data.total_invoices)} icon={FileText} />
            <StatCard label="Outstanding Balance" value={formatCurrency(data.outstanding_amount)} icon={IndianRupee} />
          </div>

          {/* Activity Grid */}
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Recent Subscriptions */}
            <div className="rounded-xl border border-gray-200 bg-white shadow-xs">
              <div className="flex items-center justify-between border-b border-gray-200 px-5 py-4">
                <div className="flex items-center gap-2">
                  <Repeat className="size-4 text-brand-700" />
                  <h2 className="text-base font-semibold text-gray-900">Recent Subscriptions</h2>
                </div>
                <Link
                  to="/subscriptions"
                  className="flex items-center gap-1 text-xs font-medium text-brand-700 hover:text-brand-900 hover:underline"
                >
                  View all
                  <ArrowRight className="size-3" />
                </Link>
              </div>

              <div className="p-2">
                {data.recent_subscriptions && data.recent_subscriptions.length > 0 ? (
                  <div className="divide-y divide-gray-100">
                    {data.recent_subscriptions.slice(0, 5).map((sub) => (
                      <div
                        key={sub.id}
                        className="flex items-center justify-between p-3 hover:bg-gray-50/80 rounded-lg transition-colors"
                      >
                        <div className="min-w-0 pr-3">
                          <p className="truncate text-sm font-medium text-gray-900">
                            {sub.customer_name || `Customer #${sub.id}`}
                          </p>
                          <p className="truncate text-xs text-gray-500">
                            {sub.plan_name} • {formatCurrency(sub.price)}
                          </p>
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                          <StatusBadge status={sub.status} />
                          <span className="text-xs text-gray-400">
                            {formatDate(sub.start_date)}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="p-6 text-center text-sm text-gray-400">No subscriptions yet.</p>
                )}
              </div>
            </div>

            {/* Recent Payments */}
            <div className="rounded-xl border border-gray-200 bg-white shadow-xs">
              <div className="flex items-center justify-between border-b border-gray-200 px-5 py-4">
                <div className="flex items-center gap-2">
                  <CreditCard className="size-4 text-brand-700" />
                  <h2 className="text-base font-semibold text-gray-900">Recent Payments</h2>
                </div>
                <Link
                  to="/payments"
                  className="flex items-center gap-1 text-xs font-medium text-brand-700 hover:text-brand-900 hover:underline"
                >
                  View all
                  <ArrowRight className="size-3" />
                </Link>
              </div>

              <div className="p-2">
                {data.recent_payments && data.recent_payments.length > 0 ? (
                  <div className="divide-y divide-gray-100">
                    {data.recent_payments.slice(0, 5).map((pay) => (
                      <div
                        key={pay.id}
                        className="flex items-center justify-between p-3 hover:bg-gray-50/80 rounded-lg transition-colors"
                      >
                        <div className="min-w-0 pr-3">
                          <p className="truncate text-sm font-medium text-gray-900">
                            {pay.invoice_number || `INV-${pay.id}`}
                          </p>
                          <p className="truncate text-xs text-gray-500">
                            {pay.customer_name || 'Customer'} • {titleCase(pay.method || 'card')}
                          </p>
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                          <span className="text-sm font-semibold text-brand-900">
                            {formatCurrency(pay.amount)}
                          </span>
                          <StatusBadge status={pay.status} />
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="p-6 text-center text-sm text-gray-400">No payments recorded yet.</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

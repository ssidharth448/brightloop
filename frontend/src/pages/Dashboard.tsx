import { FileText, IndianRupee, Repeat, TrendingUp, Users } from 'lucide-react'
import { StatCard } from '../components/dashboard/StatCard'
import { ErrorState } from '../components/ui/ErrorState'
import { PageHeader } from '../components/ui/PageHeader'
import { PageLoader } from '../components/ui/Spinner'
import { useFetch } from '../hooks/useFetch'
import { formatCurrency } from '../lib/format'
import { api } from '../services/api'

// Foundation version: proves the API client and mock work. Recent payments/subscriptions tables and charts come next.
export default function Dashboard() {
  const { data, loading, error, reload } = useFetch(api.dashboard)

  return (
    <>
      <PageHeader title="Dashboard" description="How your subscription business is doing right now." />
      {loading && <PageLoader />}
      {error && <ErrorState message={error} onRetry={reload} />}
      {data && (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
          <StatCard label="Customers" value={String(data.total_customers)} icon={Users} />
          <StatCard label="Active subscriptions" value={String(data.active_subscriptions)} icon={Repeat} />
          <StatCard label="Monthly recurring revenue" value={formatCurrency(data.mrr)} icon={TrendingUp} />
          <StatCard label="Invoices" value={String(data.total_invoices)} icon={FileText} />
          <StatCard label="Outstanding" value={formatCurrency(data.outstanding_amount)} icon={IndianRupee} />
        </div>
      )}
    </>
  )
}

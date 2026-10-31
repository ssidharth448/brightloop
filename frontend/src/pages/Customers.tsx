import { Users } from 'lucide-react'
import { EmptyState } from '../components/ui/EmptyState'
import { PageHeader } from '../components/ui/PageHeader'

// Placeholder: the full Customers page is built next.
export default function Customers() {
  return (
    <>
      <PageHeader title="Customers" description="Everyone who subscribes to your plans." />
      <EmptyState icon={Users} title="This page is not built yet" description="The customer list and forms arrive in the next step." />
    </>
  )
}

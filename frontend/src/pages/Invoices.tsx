import { FileText } from 'lucide-react'
import { EmptyState } from '../components/ui/EmptyState'
import { PageHeader } from '../components/ui/PageHeader'

// Placeholder: the full Invoices page is built next.
export default function Invoices() {
  return (
    <>
      <PageHeader title="Invoices" description="Review what has been billed and what is still owed." />
      <EmptyState icon={FileText} title="This page is not built yet" description="The invoice list and forms arrive in the next step." />
    </>
  )
}

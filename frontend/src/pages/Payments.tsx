import { CreditCard } from 'lucide-react'
import { EmptyState } from '../components/ui/EmptyState'
import { PageHeader } from '../components/ui/PageHeader'

// Placeholder: the full Payments page is built next.
export default function Payments() {
  return (
    <>
      <PageHeader title="Payments" description="Every payment recorded against an invoice." />
      <EmptyState icon={CreditCard} title="This page is not built yet" description="The payment list and forms arrive in the next step." />
    </>
  )
}

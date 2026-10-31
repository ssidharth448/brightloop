import { Repeat } from 'lucide-react'
import { EmptyState } from '../components/ui/EmptyState'
import { PageHeader } from '../components/ui/PageHeader'

// Placeholder: the full Subscriptions page is built next.
export default function Subscriptions() {
  return (
    <>
      <PageHeader title="Subscriptions" description="Track who is subscribed to what, and when they are billed next." />
      <EmptyState icon={Repeat} title="This page is not built yet" description="The subscription list and forms arrive in the next step." />
    </>
  )
}

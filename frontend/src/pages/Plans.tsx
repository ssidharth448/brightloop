import { Layers } from 'lucide-react'
import { EmptyState } from '../components/ui/EmptyState'
import { PageHeader } from '../components/ui/PageHeader'

// Placeholder: the full Plans page is built next.
export default function Plans() {
  return (
    <>
      <PageHeader title="Plans" description="Define what customers pay and how often." />
      <EmptyState icon={Layers} title="This page is not built yet" description="The plan list and forms arrive in the next step." />
    </>
  )
}

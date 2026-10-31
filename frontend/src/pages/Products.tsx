import { Package } from 'lucide-react'
import { EmptyState } from '../components/ui/EmptyState'
import { PageHeader } from '../components/ui/PageHeader'

// Placeholder: the full Products page is built next.
export default function Products() {
  return (
    <>
      <PageHeader title="Products" description="Create products and manage their variants." />
      <EmptyState icon={Package} title="This page is not built yet" description="The product list and forms arrive in the next step." />
    </>
  )
}

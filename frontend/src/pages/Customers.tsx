import { useMemo, useState, type FormEvent } from 'react'
import { Building2, Edit2, Mail, Phone, Plus, Users } from 'lucide-react'
import { Button } from '../components/ui/Button'
import { EmptyState } from '../components/ui/EmptyState'
import { ErrorState } from '../components/ui/ErrorState'
import { Input } from '../components/ui/Input'
import { Modal } from '../components/ui/Modal'
import { PageHeader } from '../components/ui/PageHeader'
import { SearchBar } from '../components/ui/SearchBar'
import { PageLoader } from '../components/ui/Spinner'
import { useFetch } from '../hooks/useFetch'
import { useToast } from '../hooks/useToast'
import { formatDate } from '../lib/format'
import { api } from '../services/api'
import type { Customer, CustomerInput } from '../types'

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export default function Customers() {
  const { data: customers, loading, error, reload } = useFetch(api.customers.list)
  const toast = useToast()

  const [search, setSearch] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editingCustomer, setEditingCustomer] = useState<Customer | null>(null)
  const [submitting, setSubmitting] = useState(false)

  // Form fields
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [company, setCompany] = useState('')
  const [formErrors, setFormErrors] = useState<{ name?: string; email?: string }>({})

  const filteredCustomers = useMemo(() => {
    if (!customers) return []
    const q = search.trim().toLowerCase()
    if (!q) return customers
    return customers.filter(
      (c) =>
        c.name.toLowerCase().includes(q) ||
        c.email.toLowerCase().includes(q) ||
        (c.company && c.company.toLowerCase().includes(q)) ||
        (c.phone && c.phone.toLowerCase().includes(q))
    )
  }, [customers, search])

  function openCreateModal() {
    setEditingCustomer(null)
    setName('')
    setEmail('')
    setPhone('')
    setCompany('')
    setFormErrors({})
    setModalOpen(true)
  }

  function openEditModal(cust: Customer) {
    setEditingCustomer(cust)
    setName(cust.name)
    setEmail(cust.email)
    setPhone(cust.phone || '')
    setCompany(cust.company || '')
    setFormErrors({})
    setModalOpen(true)
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const errors: typeof formErrors = {}
    if (!name.trim()) errors.name = 'Full name is required.'
    if (!email.trim()) errors.email = 'Email address is required.'
    else if (!EMAIL_RE.test(email.trim())) errors.email = 'Enter a valid email address.'
    setFormErrors(errors)
    if (Object.keys(errors).length) return

    setSubmitting(true)
    try {
      const payload: CustomerInput = {
        name: name.trim(),
        email: email.trim(),
        phone: phone.trim(),
        company: company.trim(),
      }
      if (editingCustomer) {
        await api.customers.update(editingCustomer.id, payload)
        toast.success(`Updated ${payload.name}`)
      } else {
        await api.customers.create(payload)
        toast.success(`Registered customer ${payload.name}`)
      }
      setModalOpen(false)
      reload()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to save customer.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <PageHeader
        title="Customers"
        description="Everyone who subscribes to your software plans and receives invoices."
        actions={
          <Button onClick={openCreateModal}>
            <Plus className="size-4" />
            New Customer
          </Button>
        }
      />

      <div className="mb-6 flex items-center justify-between gap-4">
        <SearchBar value={search} onChange={setSearch} placeholder="Search by name, email, company…" />
      </div>

      {loading && <PageLoader />}
      {error && <ErrorState message={error} onRetry={reload} />}

      {!loading && !error && filteredCustomers.length === 0 && (
        <EmptyState
          icon={Users}
          title={search ? 'No matching customers' : 'No customers yet'}
          description={
            search
              ? 'Try searching with a different term.'
              : 'Add your first customer to subscribe them to plans.'
          }
          action={
            !search && (
              <Button onClick={openCreateModal}>
                <Plus className="size-4" />
                Add Customer
              </Button>
            )
          }
        />
      )}

      {!loading && !error && filteredCustomers.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-gray-700">
              <thead className="border-b border-gray-200 bg-gray-50 text-xs font-medium text-gray-500 uppercase tracking-wider">
                <tr>
                  <th scope="col" className="px-6 py-3.5">Customer</th>
                  <th scope="col" className="px-6 py-3.5">Company</th>
                  <th scope="col" className="px-6 py-3.5">Contact</th>
                  <th scope="col" className="px-6 py-3.5">Joined</th>
                  <th scope="col" className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filteredCustomers.map((c) => (
                  <tr key={c.id} className="hover:bg-gray-50/80 transition-colors">
                    <td className="px-6 py-4 font-medium text-gray-900 whitespace-nowrap">
                      <div className="flex items-center gap-3">
                        <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-brand-100 font-semibold text-brand-800">
                          {c.name.charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <div>{c.name}</div>
                          <div className="text-xs text-gray-400">ID: {c.id}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-600">
                      {c.company ? (
                        <div className="flex items-center gap-1.5">
                          <Building2 className="size-3.5 text-gray-400" />
                          <span>{c.company}</span>
                        </div>
                      ) : (
                        <span className="text-gray-400">—</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex flex-col gap-0.5 text-xs text-gray-500">
                        <div className="flex items-center gap-1.5">
                          <Mail className="size-3.5 text-gray-400" />
                          <span className="text-gray-700">{c.email}</span>
                        </div>
                        {c.phone && (
                          <div className="flex items-center gap-1.5">
                            <Phone className="size-3.5 text-gray-400" />
                            <span>{c.phone}</span>
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-xs text-gray-500">
                      {c.created_at ? formatDate(c.created_at) : '—'}
                    </td>
                    <td className="px-6 py-4 text-right whitespace-nowrap">
                      <Button variant="ghost" size="sm" onClick={() => openEditModal(c)}>
                        <Edit2 className="size-3.5" />
                        Edit
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Customer Create/Edit Modal */}
      <Modal
        open={modalOpen}
        title={editingCustomer ? `Edit ${editingCustomer.name}` : 'New Customer'}
        onClose={() => setModalOpen(false)}
        footer={
          <>
            <Button variant="secondary" onClick={() => setModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSubmit} loading={submitting}>
              {editingCustomer ? 'Save Changes' : 'Create Customer'}
            </Button>
          </>
        }
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Full Name"
            placeholder="e.g. Asha Menon"
            value={name}
            onChange={(e) => setName(e.target.value)}
            error={formErrors.name}
            required
          />
          <Input
            label="Email Address"
            type="email"
            placeholder="asha@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            error={formErrors.email}
            required
          />
          <Input
            label="Phone Number"
            placeholder="+91 98470 11223"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
          />
          <Input
            label="Company"
            placeholder="e.g. Kaveri Textiles"
            value={company}
            onChange={(e) => setCompany(e.target.value)}
          />
        </form>
      </Modal>
    </>
  )
}

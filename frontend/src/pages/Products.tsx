import { useMemo, useState, type FormEvent } from 'react'
import { Plus, Tag, Trash2, Edit2 } from 'lucide-react'
import { StatusBadge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { ConfirmDialog } from '../components/ui/ConfirmDialog'
import { EmptyState } from '../components/ui/EmptyState'
import { ErrorState } from '../components/ui/ErrorState'
import { Input, Textarea } from '../components/ui/Input'
import { Modal } from '../components/ui/Modal'
import { PageHeader } from '../components/ui/PageHeader'
import { SearchBar } from '../components/ui/SearchBar'
import { PageLoader } from '../components/ui/Spinner'
import { useFetch } from '../hooks/useFetch'
import { useToast } from '../hooks/useToast'
import { formatCurrency, formatDate } from '../lib/format'
import { api } from '../services/api'
import type { Product, ProductInput, VariantInput } from '../types'

export default function Products() {
  const { data: products, loading, error, reload } = useFetch(api.products.list)
  const toast = useToast()

  const [search, setSearch] = useState('')
  const [productModalOpen, setProductModalOpen] = useState(false)
  const [editingProduct, setEditingProduct] = useState<Product | null>(null)
  const [variantModalProduct, setVariantModalProduct] = useState<Product | null>(null)
  const [deleteProductTarget, setDeleteProductTarget] = useState<Product | null>(null)
  const [submitting, setSubmitting] = useState(false)

  // Product Form state
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [basePrice, setBasePrice] = useState('')
  const [active, setActive] = useState(true)
  const [formErrors, setFormErrors] = useState<{ name?: string; basePrice?: string }>({})

  // Variant Form state
  const [varName, setVarName] = useState('')
  const [varSku, setVarSku] = useState('')
  const [varExtraPrice, setVarExtraPrice] = useState('0')
  const [varErrors, setVarErrors] = useState<{ name?: string; sku?: string }>({})

  const filteredProducts = useMemo(() => {
    if (!products) return []
    const q = search.trim().toLowerCase()
    if (!q) return products
    return products.filter(
      (p) =>
        p.name.toLowerCase().includes(q) ||
        (p.description && p.description.toLowerCase().includes(q))
    )
  }, [products, search])

  function openCreateModal() {
    setEditingProduct(null)
    setName('')
    setDescription('')
    setBasePrice('')
    setActive(true)
    setFormErrors({})
    setProductModalOpen(true)
  }

  function openEditModal(prod: Product) {
    setEditingProduct(prod)
    setName(prod.name)
    setDescription(prod.description || '')
    setBasePrice(String(prod.base_price))
    setActive(prod.active)
    setFormErrors({})
    setProductModalOpen(true)
  }

  function openVariantModal(prod: Product) {
    setVariantModalProduct(prod)
    setVarName('')
    setVarSku('')
    setVarExtraPrice('0')
    setVarErrors({})
  }

  async function handleProductSubmit(e: FormEvent) {
    e.preventDefault()
    const errors: typeof formErrors = {}
    if (!name.trim()) errors.name = 'Product name is required.'
    const priceNum = parseFloat(basePrice)
    if (isNaN(priceNum) || priceNum < 0) errors.basePrice = 'Enter a valid non-negative price.'
    setFormErrors(errors)
    if (Object.keys(errors).length) return

    setSubmitting(true)
    try {
      const payload: ProductInput = {
        name: name.trim(),
        description: description.trim(),
        base_price: priceNum,
        active,
      }
      if (editingProduct) {
        await api.products.update(editingProduct.id, payload)
        toast.success(`Updated ${payload.name}`)
      } else {
        await api.products.create(payload)
        toast.success(`Created product ${payload.name}`)
      }
      setProductModalOpen(false)
      reload()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to save product.')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleVariantSubmit(e: FormEvent) {
    e.preventDefault()
    if (!variantModalProduct) return
    const errors: typeof varErrors = {}
    if (!varName.trim()) errors.name = 'Variant name is required.'
    if (!varSku.trim()) errors.sku = 'SKU is required.'
    setVarErrors(errors)
    if (Object.keys(errors).length) return

    setSubmitting(true)
    try {
      const payload: VariantInput = {
        name: varName.trim(),
        sku: varSku.trim().toUpperCase(),
        extra_price: parseFloat(varExtraPrice) || 0,
      }
      await api.products.addVariant(variantModalProduct.id, payload)
      toast.success(`Added variant ${payload.name}`)
      setVariantModalProduct(null)
      reload()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to add variant.')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleDeleteConfirm() {
    if (!deleteProductTarget) return
    setSubmitting(true)
    try {
      await api.products.remove(deleteProductTarget.id)
      toast.success(`Deactivated ${deleteProductTarget.name}`)
      setDeleteProductTarget(null)
      reload()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to delete product.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <PageHeader
        title="Products"
        description="Create products and manage their pricing and variants."
        actions={
          <Button onClick={openCreateModal}>
            <Plus className="size-4" />
            New Product
          </Button>
        }
      />

      <div className="mb-6 flex items-center justify-between gap-4">
        <SearchBar value={search} onChange={setSearch} placeholder="Search products…" />
      </div>

      {loading && <PageLoader />}
      {error && <ErrorState message={error} onRetry={reload} />}

      {!loading && !error && filteredProducts.length === 0 && (
        <EmptyState
          icon={Tag}
          title={search ? 'No matching products' : 'No products yet'}
          description={
            search
              ? 'Try adjusting your search query.'
              : 'Add your first product to begin building subscription plans.'
          }
          action={
            !search && (
              <Button onClick={openCreateModal}>
                <Plus className="size-4" />
                Add Product
              </Button>
            )
          }
        />
      )}

      {!loading && !error && filteredProducts.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filteredProducts.map((p) => (
            <div
              key={p.id}
              className="flex flex-col justify-between rounded-xl border border-gray-200 bg-white p-5 shadow-xs transition-shadow hover:shadow-sm"
            >
              <div>
                <div className="flex items-start justify-between gap-2">
                  <h3 className="text-base font-semibold text-gray-900">{p.name}</h3>
                  <StatusBadge status={p.active ? 'active' : 'inactive'} />
                </div>
                <p className="mt-2 text-sm text-gray-500 line-clamp-2">
                  {p.description || 'No description provided.'}
                </p>
                <div className="mt-4 flex items-baseline gap-1">
                  <span className="text-2xl font-bold tracking-tight text-gray-900">
                    {formatCurrency(p.base_price)}
                  </span>
                  <span className="text-xs text-gray-500">base price</span>
                </div>

                {/* Variants preview */}
                <div className="mt-4 border-t border-gray-100 pt-3">
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span className="font-medium text-gray-700">
                      Variants ({p.variants?.length || 0})
                    </span>
                    <button
                      type="button"
                      onClick={() => openVariantModal(p)}
                      className="font-medium text-brand-700 hover:text-brand-900 hover:underline"
                    >
                      + Add Variant
                    </button>
                  </div>
                  {p.variants && p.variants.length > 0 ? (
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {p.variants.map((v) => (
                        <span
                          key={v.id}
                          className="inline-flex items-center gap-1 rounded bg-gray-50 px-2 py-0.5 text-xs text-gray-600 ring-1 ring-inset ring-gray-200"
                        >
                          <span className="font-medium">{v.name}</span>
                          <span className="text-gray-400">({v.sku})</span>
                          {v.extra_price > 0 && (
                            <span className="text-brand-700">+{formatCurrency(v.extra_price)}</span>
                          )}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="mt-1 text-xs italic text-gray-400">No variants added.</p>
                  )}
                </div>
              </div>

              <div className="mt-5 flex items-center justify-between border-t border-gray-100 pt-3 text-xs text-gray-400">
                <span>Created {p.created_at ? formatDate(p.created_at) : 'recently'}</span>
                <div className="flex items-center gap-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => openEditModal(p)}
                    aria-label={`Edit ${p.name}`}
                  >
                    <Edit2 className="size-3.5" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-red-600 hover:bg-red-50 hover:text-red-700"
                    onClick={() => setDeleteProductTarget(p)}
                    aria-label={`Delete ${p.name}`}
                  >
                    <Trash2 className="size-3.5" />
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Product Create/Edit Modal */}
      <Modal
        open={productModalOpen}
        title={editingProduct ? `Edit ${editingProduct.name}` : 'New Product'}
        onClose={() => setProductModalOpen(false)}
        footer={
          <>
            <Button variant="secondary" onClick={() => setProductModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleProductSubmit} loading={submitting}>
              {editingProduct ? 'Save Changes' : 'Create Product'}
            </Button>
          </>
        }
      >
        <form onSubmit={handleProductSubmit} className="space-y-4">
          <Input
            label="Product Name"
            placeholder="e.g. Brightloop CRM"
            value={name}
            onChange={(e) => setName(e.target.value)}
            error={formErrors.name}
            required
          />
          <Textarea
            label="Description"
            placeholder="Describe what is included in this product…"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
          <Input
            label="Base Price (INR)"
            type="number"
            step="0.01"
            min="0"
            placeholder="1200.00"
            value={basePrice}
            onChange={(e) => setBasePrice(e.target.value)}
            error={formErrors.basePrice}
            required
          />
          <label className="flex items-center gap-2 pt-1 text-sm font-medium text-gray-800">
            <input
              type="checkbox"
              checked={active}
              onChange={(e) => setActive(e.target.checked)}
              className="size-4 rounded border-gray-300 text-brand-800 focus:ring-brand-700"
            />
            Product is Active
          </label>
        </form>
      </Modal>

      {/* Add Variant Modal */}
      <Modal
        open={Boolean(variantModalProduct)}
        title={`Add Variant to ${variantModalProduct?.name}`}
        onClose={() => setVariantModalProduct(null)}
        footer={
          <>
            <Button variant="secondary" onClick={() => setVariantModalProduct(null)}>
              Cancel
            </Button>
            <Button onClick={handleVariantSubmit} loading={submitting}>
              Add Variant
            </Button>
          </>
        }
      >
        <form onSubmit={handleVariantSubmit} className="space-y-4">
          <Input
            label="Variant Name"
            placeholder="e.g. Starter (5 seats)"
            value={varName}
            onChange={(e) => setVarName(e.target.value)}
            error={varErrors.name}
            required
          />
          <Input
            label="SKU"
            placeholder="e.g. CRM-S5"
            value={varSku}
            onChange={(e) => setVarSku(e.target.value)}
            error={varErrors.sku}
            required
          />
          <Input
            label="Extra Price (INR)"
            type="number"
            step="0.01"
            min="0"
            placeholder="0"
            value={varExtraPrice}
            onChange={(e) => setVarExtraPrice(e.target.value)}
            hint="Added on top of the base product price."
          />
        </form>
      </Modal>

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={Boolean(deleteProductTarget)}
        title="Deactivate Product"
        message={`Are you sure you want to deactivate "${deleteProductTarget?.name}"? Existing subscriptions will remain intact.`}
        confirmLabel="Deactivate"
        danger
        loading={submitting}
        onConfirm={handleDeleteConfirm}
        onCancel={() => setDeleteProductTarget(null)}
      />
    </>
  )
}

import { Loader2 } from 'lucide-react'

export function Spinner({ className = 'size-5' }: { className?: string }) {
  return <Loader2 className={`animate-spin ${className}`} aria-hidden="true" />
}

export function PageLoader({ label = 'Loading…' }: { label?: string }) {
  return (
    <div className="flex min-h-64 items-center justify-center gap-3 text-sm text-gray-500" role="status">
      <Spinner className="size-5 text-brand-700" />
      {label}
    </div>
  )
}

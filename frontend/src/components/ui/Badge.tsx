import type { ReactNode } from 'react'
import { titleCase } from '../../lib/format'

type Tone = 'green' | 'amber' | 'red' | 'gray'

const tones: Record<Tone, string> = {
  green: 'bg-brand-100 text-brand-900 ring-brand-400/50',
  amber: 'bg-amber-50 text-amber-800 ring-amber-300/60',
  red: 'bg-red-50 text-red-700 ring-red-300/60',
  gray: 'bg-gray-100 text-gray-600 ring-gray-300/60',
}

export function Badge({ tone = 'gray', children }: { tone?: Tone; children: ReactNode }) {
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${tones[tone]}`}>
      {children}
    </span>
  )
}

const statusTone: Record<string, Tone> = {
  active: 'green',
  paid: 'green',
  succeeded: 'green',
  paused: 'amber',
  partial: 'amber',
  pending: 'amber',
  draft: 'gray',
  expired: 'gray',
  void: 'gray',
  inactive: 'gray',
  cancelled: 'red',
  failed: 'red',
  unpaid: 'red',
}

/** One badge for every status in the app (subscription, invoice, payment, plan). */
export function StatusBadge({ status }: { status: string }) {
  return <Badge tone={statusTone[status] ?? 'gray'}>{titleCase(status)}</Badge>
}

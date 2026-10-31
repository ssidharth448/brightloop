import { LogOut, Menu } from 'lucide-react'
import { useLocation } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import { Button } from '../ui/Button'
import { NAV_ITEMS } from './nav'

export function Header({ onMenu }: { onMenu: () => void }) {
  const { user, logout } = useAuth()
  const { pathname } = useLocation()
  const current = NAV_ITEMS.find((item) => (item.to === '/' ? pathname === '/' : pathname.startsWith(item.to)))

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-gray-200 bg-white px-4 sm:px-6 lg:px-8">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onMenu}
          className="rounded-md p-2 text-gray-600 hover:bg-gray-100 lg:hidden"
          aria-label="Open navigation"
        >
          <Menu className="size-5" />
        </button>
        <span className="text-sm font-medium text-gray-700">{current?.label ?? 'Brightloop'}</span>
      </div>
      <div className="flex items-center gap-3">
        <div className="hidden text-right sm:block">
          <div className="flex items-center justify-end gap-1.5">
            <p className="text-sm font-medium leading-tight text-gray-900">{user?.name}</p>
            <span className="rounded bg-brand-100 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-brand-800">
              {user?.role || 'staff'}
            </span>
          </div>
          <p className="text-xs text-gray-500">{user?.email}</p>
        </div>
        <div className="flex size-9 items-center justify-center rounded-full bg-brand-900 text-sm font-semibold text-brand-400" aria-hidden="true">
          {user?.name?.charAt(0).toUpperCase()}
        </div>
        <Button variant="ghost" size="sm" onClick={logout}>
          <LogOut className="size-4" />
          Sign out
        </Button>
      </div>
    </header>
  )
}

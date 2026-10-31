import { useState, type FormEvent } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { Logo } from '../components/layout/Logo'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Select } from '../components/ui/Select'
import { useAuth } from '../hooks/useAuth'

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export default function Login() {
  const { user, login, register } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = (location.state as { from?: string } | null)?.from ?? '/'

  const [mode, setMode] = useState<'signin' | 'register'>('signin')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState<'staff' | 'admin'>('staff')

  const [errors, setErrors] = useState<{ name?: string; email?: string; password?: string }>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  if (user) return <Navigate to={from} replace />

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const next: typeof errors = {}
    if (mode === 'register' && !name.trim()) next.name = 'Enter your full name.'
    if (!email.trim()) next.email = 'Enter your email address.'
    else if (!EMAIL_RE.test(email.trim())) next.email = 'Enter a valid email address.'
    if (!password) next.password = 'Enter your password.'
    else if (mode === 'register' && password.length < 6) next.password = 'Password must be at least 6 characters.'
    setErrors(next)
    setFormError(null)
    if (Object.keys(next).length) return

    setSubmitting(true)
    try {
      if (mode === 'register') {
        await register({ name: name.trim(), email: email.trim(), password, role })
      } else {
        await login(email.trim(), password)
      }
      navigate(from, { replace: true })
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Authentication failed. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  function handleQuickFill(fillEmail: string, fillPass: string) {
    setMode('signin')
    setEmail(fillEmail)
    setPassword(fillPass)
    setFormError(null)
    setErrors({})
  }

  return (
    <div className="grid min-h-screen lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]">
      <div className="hidden flex-col justify-between bg-brand-900 p-12 lg:flex">
        <Logo />
        <div className="max-w-md">
          <h2 className="text-3xl font-semibold leading-tight tracking-tight text-white">
            Every subscription, invoice and payment in one place.
          </h2>
          <p className="mt-4 text-base text-white/70">
            Set up a plan, subscribe a customer and watch the billing cycle run, from first invoice to final payment.
          </p>
        </div>
        <p className="text-sm text-white/40">Brightloop subscription management</p>
      </div>

      <div className="flex items-center justify-center bg-white px-6 py-12">
        <div className="w-full max-w-sm">
          <div className="mb-8 lg:hidden">
            <div className="inline-flex rounded-lg bg-brand-900 px-3 py-2">
              <Logo />
            </div>
          </div>

          {/* Mode Switch Tabs */}
          <div className="flex rounded-lg bg-gray-100 p-1 mb-6">
            <button
              type="button"
              onClick={() => {
                setMode('signin')
                setFormError(null)
                setErrors({})
              }}
              className={`flex-1 rounded-md py-1.5 text-xs font-semibold transition-colors cursor-pointer ${
                mode === 'signin' ? 'bg-white text-gray-900 shadow-xs' : 'text-gray-500 hover:text-gray-900'
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => {
                setMode('register')
                setFormError(null)
                setErrors({})
              }}
              className={`flex-1 rounded-md py-1.5 text-xs font-semibold transition-colors cursor-pointer ${
                mode === 'register' ? 'bg-white text-gray-900 shadow-xs' : 'text-gray-500 hover:text-gray-900'
              }`}
            >
              Register User
            </button>
          </div>

          <h1 className="text-2xl font-semibold tracking-tight text-gray-900">
            {mode === 'signin' ? 'Sign in' : 'Create an account'}
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            {mode === 'signin'
              ? 'Sign in as Administrator or Staff User.'
              : 'Register a new team member or administrator.'}
          </p>

          <form onSubmit={handleSubmit} noValidate className="mt-6 space-y-4">
            {formError && (
              <div role="alert" className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                {formError}
              </div>
            )}

            {mode === 'register' && (
              <Input
                label="Full Name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                error={errors.name}
                placeholder="Alex Morgan"
                required
              />
            )}

            <Input
              label="Email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              error={errors.email}
              placeholder="you@company.com"
              required
            />

            <Input
              label="Password"
              type="password"
              autoComplete={mode === 'signin' ? 'current-password' : 'new-password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              error={errors.password}
              hint={mode === 'register' ? 'At least 6 characters' : undefined}
              required
            />

            {mode === 'register' && (
              <Select
                label="Role"
                value={role}
                onChange={(e) => setRole(e.target.value as 'staff' | 'admin')}
              >
                <option value="staff">Staff User (Standard Access)</option>
                <option value="admin">Administrator (Full Access)</option>
              </Select>
            )}

            <Button type="submit" className="w-full" loading={submitting}>
              {submitting
                ? mode === 'signin'
                  ? 'Signing in…'
                  : 'Registering…'
                : mode === 'signin'
                ? 'Sign in'
                : 'Create Account'}
            </Button>
          </form>

          {/* Quick login helper credentials */}
          <div className="mt-8 rounded-lg border border-gray-200 bg-gray-50 p-3 text-xs text-gray-600">
            <span className="font-semibold text-gray-800">Quick Test Credentials:</span>
            <div className="mt-2 flex flex-col gap-2">
              <div className="flex items-center justify-between border-b border-gray-200/80 pb-1.5">
                <div>
                  <span className="font-semibold text-gray-900">Admin: </span>
                  <span className="font-mono text-gray-700">admin@brightloop.com</span>
                  <div className="text-[11px] text-gray-400">Pass: admin123</div>
                </div>
                <button
                  type="button"
                  onClick={() => handleQuickFill('admin@brightloop.com', 'admin123')}
                  className="font-medium text-brand-700 hover:text-brand-900 hover:underline cursor-pointer"
                >
                  Use Admin
                </button>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <span className="font-semibold text-gray-900">Staff User: </span>
                  <span className="font-mono text-gray-700">user@brightloop.com</span>
                  <div className="text-[11px] text-gray-400">Pass: user123</div>
                </div>
                <button
                  type="button"
                  onClick={() => handleQuickFill('user@brightloop.com', 'user123')}
                  className="font-medium text-brand-700 hover:text-brand-900 hover:underline cursor-pointer"
                >
                  Use Staff
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

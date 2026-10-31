const BASE_URL = (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8000/api'
const TOKEN_KEY = 'brightloop_token'

export const tokenStore = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (token: string) => localStorage.setItem(TOKEN_KEY, token),
  clear: () => localStorage.removeItem(TOKEN_KEY),
}

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

// AuthContext registers a callback here so a 401 anywhere logs the user out.
let onUnauthorized: (() => void) | null = null
export function setUnauthorizedHandler(fn: (() => void) | null) {
  onUnauthorized = fn
}

interface RequestOptions {
  method?: string
  body?: unknown
  /** Send as application/x-www-form-urlencoded (FastAPI OAuth2 login style). */
  form?: Record<string, string>
}

export async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = { Accept: 'application/json' }
  const token = tokenStore.get()
  if (token) headers.Authorization = `Bearer ${token}`

  let body: BodyInit | undefined
  if (opts.form) {
    headers['Content-Type'] = 'application/x-www-form-urlencoded'
    body = new URLSearchParams(opts.form)
  } else if (opts.body !== undefined) {
    headers['Content-Type'] = 'application/json'
    body = JSON.stringify(opts.body)
  }

  let res: Response
  try {
    res = await fetch(`${BASE_URL}${path}`, { method: opts.method ?? 'GET', headers, body })
  } catch {
    throw new ApiError('Cannot reach the server. Check that the backend is running.', 0)
  }

  if (res.status === 401 && !path.startsWith('/auth/login')) {
    tokenStore.clear()
    onUnauthorized?.()
  }

  if (!res.ok) {
    let message = `Request failed (${res.status})`
    try {
      const data = await res.json()
      const detail = data?.detail ?? data?.message
      if (typeof detail === 'string') {
        message = detail
      } else if (Array.isArray(detail)) {
        // FastAPI validation errors: [{ loc, msg, type }]
        const msgs = detail.map((d: { msg?: string }) => d.msg).filter(Boolean)
        if (msgs.length) message = msgs.join(', ')
      }
    } catch {
      // response had no JSON body
    }
    throw new ApiError(message, res.status)
  }

  if (res.status === 204) return undefined as T
  return (await res.json()) as T
}

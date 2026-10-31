import type { ApiService } from '../types'
import { mockApi } from './mockApi'
import { realApi } from './realApi'

/** Set VITE_USE_MOCK=false in .env to talk to the real FastAPI backend. */
export const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

export const api: ApiService = USE_MOCK ? mockApi : realApi

export { ApiError, setUnauthorizedHandler, tokenStore } from './http'

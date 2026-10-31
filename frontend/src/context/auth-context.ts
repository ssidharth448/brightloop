import { createContext } from 'react'
import type { User, UserRegisterInput } from '../types'

export interface AuthState {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (data: UserRegisterInput) => Promise<void>
  logout: () => void
}

export const AuthContext = createContext<AuthState | null>(null)

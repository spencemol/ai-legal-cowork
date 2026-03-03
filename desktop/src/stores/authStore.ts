import { create } from 'zustand'
import type { User } from '../types'

interface AuthState {
  token: string | null
  user: User | null
  login: (token: string, user: User) => void
  logout: () => void
  isAuthenticated: () => boolean
}

export const useAuthStore = create<AuthState>()((set, get) => ({
  token: null,
  user: null,
  login: (token: string, user: User) => set({ token, user }),
  logout: () => set({ token: null, user: null }),
  isAuthenticated: () => get().token !== null,
}))

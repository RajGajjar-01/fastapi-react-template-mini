import axios from 'axios'
import { create } from 'zustand'
import { api, registerAuthReset } from '@/lib/api'

export interface AuthUserProfile {
  user_id: string
  email: string
  full_name: string | null
  avatar_url: string | null
}

interface AuthState {
  user: AuthUserProfile | null
  loading: boolean
  error: string | null
}

interface AuthActions {
  initialize: () => Promise<void>
  login: (email: string, password: string) => Promise<void>
  signup: (email: string, password: string, full_name?: string | null) => Promise<void>
  logout: () => Promise<void>
  updateProfile: (full_name: string | null, avatar_url: string | null) => Promise<void>
  reset: () => void
}

export type AuthStore = AuthState & AuthActions

// Start with loading:true so ProtectedRoute shows a spinner (not Login)
// until initialize() completes the /auth/me check. This eliminates the
// flash-of-login-page on hard refresh.
const initialState: AuthState = {
  user: null,
  loading: true,
  error: null,
}

export const useAuthStore = create<AuthStore>((set) => {
  const reset = () => set(initialState)

  const store: AuthStore = {
    ...initialState,

    initialize: async () => {
      set({ loading: true, error: null })
      try {
        const res = await api.get<{ data: AuthUserProfile }>('/auth/me')
        set({ user: res.data.data, loading: false })
      } catch {
        set({ user: null, loading: false })
      }
    },

    login: async (email: string, password: string) => {
      set({ loading: true, error: null })
      try {
        await api.post('/auth/login', { email, password })
        const res = await api.get<{ data: AuthUserProfile }>('/auth/me')
        set({ user: res.data.data, loading: false, error: null })
      } catch (err) {
        const message = axiosErrorMessage(err) ?? 'Login failed'
        set({ user: null, loading: false, error: message })
        throw err
      }
    },

    signup: async (email: string, password: string, full_name?: string | null) => {
      set({ loading: true, error: null })
      try {
        await api.post('/auth/signup', { email, password, full_name })
        set({ loading: false, error: null })
      } catch (err) {
        const message = axiosErrorMessage(err) ?? 'Signup failed'
        set({ loading: false, error: message })
        throw err
      }
    },

    logout: async () => {
      try {
        await api.post('/auth/logout')
      } catch {
        // Ignore logout errors
      } finally {
        // loading must be false after logout so ProtectedRoute redirects
        // to /login instead of spinning indefinitely
        set({ user: null, error: null, loading: false })
      }
    },

    updateProfile: async (full_name: string | null, avatar_url: string | null) => {
      const res = await api.patch<{ data: AuthUserProfile }>('/auth/me', { full_name, avatar_url })
      set({ user: res.data.data })
    },

    reset,
  }

  registerAuthReset(reset)

  return store
})

function axiosErrorMessage(err: unknown): string | null {
  if (axios.isAxiosError(err)) {
    const body = err.response?.data as { detail?: string; message?: string } | undefined
    return body?.detail ?? body?.message ?? null
  }
  if (err instanceof Error) return err.message
  return null
}

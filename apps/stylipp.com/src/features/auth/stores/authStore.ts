import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import api, { setAuthStoreAccessor } from '@/shared/hooks/useApi'

export interface AuthUser {
  id: string
  email: string
  display_name: string | null
  onboarding_completed: boolean
}

interface AuthState {
  token: string | null
  user: AuthUser | null

  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, displayName?: string) => Promise<void>
  logout: () => void
  fetchMe: () => Promise<void>
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,

      login: async (email: string, password: string) => {
        const response = await api.post('/auth/login/', { email, password })
        const { access_token, user } = response.data
        set({ token: access_token, user })
      },

      register: async (email: string, password: string, displayName?: string) => {
        const response = await api.post('/auth/register/', {
          email,
          password,
          display_name: displayName,
        })
        const { access_token, user } = response.data
        set({ token: access_token, user })
      },

      logout: () => {
        set({ token: null, user: null })
        // Navigate to login — using window.location since we're outside React context
        window.location.href = '/login'
      },

      fetchMe: async () => {
        try {
          const response = await api.get('/auth/me/')
          set({ user: response.data })
        } catch {
          // If fetchMe fails (e.g., expired token), clear auth state
          const { token } = get()
          if (token) {
            set({ token: null, user: null })
          }
        }
      },
    }),
    {
      name: 'stylipp-auth',
      storage: createJSONStorage(() => localStorage),
      // Only persist token — fetch user on rehydration to keep onboarding_completed fresh
      partialize: (state) => ({ token: state.token }),
      onRehydrateStorage: () => {
        // After rehydration, fetch user if we have a token
        return (state?: AuthState) => {
          if (state?.token) {
            state.fetchMe()
          }
        }
      },
    }
  )
)

// Register the auth store accessor with the API client to avoid circular imports
setAuthStoreAccessor(() => useAuthStore.getState())

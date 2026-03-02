import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

/**
 * Auth store accessor — set lazily to avoid circular dependency.
 * authStore.ts calls setAuthStoreAccessor() on module load.
 */
let getAuthState: (() => { token: string | null; logout: () => void }) | null = null

export function setAuthStoreAccessor(accessor: () => { token: string | null; logout: () => void }) {
  getAuthState = accessor
}

// Request interceptor: attach JWT token if available
api.interceptors.request.use((config) => {
  const token = getAuthState?.().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor: handle 401 by clearing auth and redirecting to login
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      const state = getAuthState?.()
      // Only clear auth and redirect if we had a token (i.e., session expired)
      // Don't redirect on login/register 401 responses
      if (state?.token) {
        state.logout()
      }
    }
    return Promise.reject(error)
  }
)

export default api

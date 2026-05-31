import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL ?? ''

export const api = axios.create({
  baseURL: BASE_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
})

let _resetAuthStore: (() => void) | null = null

export function registerAuthReset(fn: () => void) {
  _resetAuthStore = fn
}

let isRefreshing = false
let failedQueue: Array<{
  resolve: (value: unknown) => void
  reject: (reason: unknown) => void
}> = []

function processQueue(error: unknown) {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(undefined)
    }
  })
  failedQueue = []
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (
      !axios.isAxiosError(error) ||
      error.response?.status !== 401 ||
      originalRequest?._retry ||
      originalRequest?.url?.includes('/auth/refresh')
    ) {
      return Promise.reject(error)
    }

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        failedQueue.push({ resolve, reject })
      }).then(() => api(originalRequest))
    }

    originalRequest._retry = true
    isRefreshing = true

    try {
      await axios.post(
        `${BASE_URL}/auth/refresh`,
        {},
        { withCredentials: true, headers: { 'Content-Type': 'application/json' } },
      )
      processQueue(null)
      return api(originalRequest)
    } catch {
      processQueue(error)
      _resetAuthStore?.()
      const publicPaths = ['/login', '/signup', '/', '/forgot-password']
      if (!publicPaths.includes(window.location.pathname)) {
        window.location.href = '/login'
      }
      return Promise.reject(error)
    } finally {
      isRefreshing = false
    }
  },
)

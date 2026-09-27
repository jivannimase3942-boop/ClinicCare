import axios, { AxiosError } from 'axios'

let rawBaseUrl = import.meta.env.VITE_API_BASE_URL || (import.meta.env.PROD ? 'https://cliniccare-backend-48g6.onrender.com/api' : 'http://localhost:8000/api')

// Ensure valid baseURL ending with /api and no trailing slashes or duplicate /api/api
let cleanBaseUrl = (rawBaseUrl || '').trim().replace(/\/+$/, '')
if (!cleanBaseUrl.endsWith('/api')) {
  cleanBaseUrl = `${cleanBaseUrl}/api`
}

export const api = axios.create({
  baseURL: cleanBaseUrl,
  timeout: 30000, // 30s timeout prevents infinite processing / spinner states
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for JWT
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('cliniccare_token') || localStorage.getItem('carepulse_token')
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string; message?: string }>) => {
    if (error.response?.status === 401) {
      const path = window.location.pathname
      if (!path.includes('/login') && !path.includes('/register')) {
        localStorage.removeItem('cliniccare_token')
        localStorage.removeItem('cliniccare_user')
        localStorage.removeItem('carepulse_token')
        localStorage.removeItem('carepulse_user')
        window.location.href = '/login'
      }
    }

    let errorMessage =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      'An unexpected error occurred'

    if (error.code === 'ECONNABORTED' || (error.message && error.message.toLowerCase().includes('timeout'))) {
      errorMessage = 'The request timed out. Render backend may be waking up from sleep. Please try again.'
    } else if (error.message === 'Network Error') {
      errorMessage = 'Unable to connect to ClinicCare server. Please check your network connection.'
    }

    return Promise.reject(new Error(errorMessage))
  }
)

export default api

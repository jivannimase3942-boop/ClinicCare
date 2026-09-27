import axios, { AxiosError } from 'axios'

const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || (import.meta.env?.PROD ? 'https://cliniccare-backend-48g6.onrender.com/api' : 'http://localhost:8000/api')

export const api = axios.create({
  baseURL: API_BASE_URL,
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
    const errorMessage =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      'An unexpected error occurred'
    return Promise.reject(new Error(errorMessage))
  }
)

export default api


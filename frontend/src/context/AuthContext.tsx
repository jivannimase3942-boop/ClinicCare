import React, { createContext, useContext, useState, useEffect } from 'react'
import { User, UserRole } from '@/types'
import { authService, LoginPayload, RegisterPayload } from '@/services/auth'
import { useToast } from './ToastContext'

interface AuthContextType {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (payload: LoginPayload) => Promise<User>
  register: (payload: RegisterPayload) => Promise<User>
  logout: () => void
  refreshUser: () => Promise<void>
  hasRole: (roles: UserRole | UserRole[]) => boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(
    () => localStorage.getItem('cliniccare_token') || localStorage.getItem('carepulse_token')
  )
  const [isLoading, setIsLoading] = useState(true)
  const { showToast } = useToast()

  const refreshUser = async () => {
    try {
      if (!token) {
        setUser(null)
        setIsLoading(false)
        return
      }
      const userData = await authService.getMe()
      setUser(userData)
      localStorage.setItem('cliniccare_user', JSON.stringify(userData))
    } catch {
      logout()
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    const storedUser = localStorage.getItem('cliniccare_user') || localStorage.getItem('carepulse_user')
    if (storedUser && token) {
      try {
        setUser(JSON.parse(storedUser))
      } catch {
        // Parse error ignored
      }
    }
    refreshUser()
  }, [token])

  const login = async (payload: LoginPayload): Promise<User> => {
    try {
      const data = await authService.login(payload)
      setToken(data.access_token)
      setUser(data.user)
      localStorage.setItem('cliniccare_token', data.access_token)
      localStorage.setItem('cliniccare_user', JSON.stringify(data.user))
      showToast(`Welcome back, ${data.user.full_name}!`, 'success')
      return data.user
    } catch (err: any) {
      showToast(err.message || 'Login failed', 'error')
      throw err
    }
  }

  const register = async (payload: RegisterPayload): Promise<User> => {
    try {
      const data = await authService.register(payload)
      setToken(data.access_token)
      setUser(data.user)
      localStorage.setItem('cliniccare_token', data.access_token)
      localStorage.setItem('cliniccare_user', JSON.stringify(data.user))
      showToast('Registration successful! Welcome to ClinicCare.', 'success')
      return data.user
    } catch (err: any) {
      showToast(err.message || 'Registration failed', 'error')
      throw err
    }
  }

  const logout = () => {
    setUser(null)
    setToken(null)
    localStorage.removeItem('cliniccare_token')
    localStorage.removeItem('cliniccare_user')
    localStorage.removeItem('carepulse_token')
    localStorage.removeItem('carepulse_user')
  }

  const hasRole = (roles: UserRole | UserRole[]): boolean => {
    if (!user) return false
    if (Array.isArray(roles)) {
      return roles.includes(user.role)
    }
    return user.role === roles
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user && !!token,
        isLoading,
        login,
        register,
        logout,
        refreshUser,
        hasRole,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

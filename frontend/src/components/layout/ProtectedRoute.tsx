import React from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { UserRole } from '@/types'
import { Loader2 } from 'lucide-react'

interface ProtectedRouteProps {
  children: React.ReactNode
  allowedRoles?: UserRole[]
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, allowedRoles }) => {
  const { user, isAuthenticated, isLoading, hasRole } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="w-8 h-8 animate-spin text-sky-600" />
          <p className="text-sm font-medium text-slate-500">Verifying security session...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  if (allowedRoles && !hasRole(allowedRoles)) {
    // If not authorized for this role, redirect to their home
    if (user.role === 'ADMIN' || user.role === 'FRONT_DESK') {
      return <Navigate to="/admin/dashboard" replace />
    }
    if (user.role === 'DOCTOR') {
      return <Navigate to="/doctor/dashboard" replace />
    }
    return <Navigate to="/patient/dashboard" replace />
  }

  return <>{children}</>
}

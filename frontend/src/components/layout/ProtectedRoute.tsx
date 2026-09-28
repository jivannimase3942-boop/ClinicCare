import React from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { UserRole } from '@/types'
import { Loader2, Clock, ShieldAlert } from 'lucide-react'

interface ProtectedRouteProps {
  children: React.ReactNode
  allowedRoles?: UserRole[]
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, allowedRoles }) => {
  const { user, isAuthenticated, isLoading, hasRole, logout } = useAuth()
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

  // Handle pending staff accounts
  if (user.role === 'PENDING_DOCTOR' || user.role === 'PENDING_FRONT_DESK') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950 px-4">
        <div className="max-w-md w-full bg-slate-900 border border-slate-800 rounded-3xl p-8 text-center shadow-2xl">
          <div className="w-16 h-16 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-400 mx-auto flex items-center justify-center mb-4">
            <Clock className="w-8 h-8" />
          </div>
          <h2 className="text-xl font-black text-white">Staff Verification in Progress</h2>
          <p className="text-sm text-slate-300 mt-2">
            Your {user.role === 'PENDING_DOCTOR' ? 'physician credential' : 'front desk onboarding'} request has been submitted to clinic administration.
          </p>
          <div className="mt-4 p-3 bg-slate-950/80 rounded-xl text-xs text-amber-400 font-mono border border-slate-800 flex items-center justify-center gap-2">
            <ShieldAlert className="w-4 h-4" />
            STATUS: PENDING ADMIN APPROVAL
          </div>
          <p className="text-xs text-slate-400 mt-3">
            An administrator will verify your credentials and activate your role. Please check back soon or contact your clinic administrator.
          </p>
          <button
            onClick={() => logout()}
            className="mt-6 w-full py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold transition border border-slate-700"
          >
            Sign Out
          </button>
        </div>
      </div>
    )
  }

  if (allowedRoles && !hasRole(allowedRoles)) {
    // If not authorized for this role, redirect to their designated role dashboard
    if (user.role === 'ADMIN') {
      return <Navigate to="/admin/dashboard" replace />
    }
    if (user.role === 'FRONT_DESK') {
      return <Navigate to="/frontdesk/dashboard" replace />
    }
    if (user.role === 'DOCTOR') {
      return <Navigate to="/doctor/dashboard" replace />
    }
    return <Navigate to="/patient/dashboard" replace />
  }

  return <>{children}</>
}


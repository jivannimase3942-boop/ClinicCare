import React from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { Button } from '@/components/ui/Button'
import { Activity, LogOut, LayoutDashboard, ShieldCheck, User } from 'lucide-react'

export const Navbar: React.FC = () => {
  const { user, isAuthenticated, logout } = useAuth()
  const navigate = useNavigate()

  const getDashboardLink = () => {
    if (!user) return '/login'
    if (user.role === 'ADMIN') return '/admin/dashboard'
    if (user.role === 'FRONT_DESK') return '/frontdesk/dashboard'
    if (user.role === 'DOCTOR') return '/doctor/dashboard'
    return '/patient/dashboard'
  }

  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-slate-200/90 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand Logo */}
        <Link to="/" className="flex items-center gap-2.5 group">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-sky-600 to-teal-500 flex items-center justify-center text-white shadow-sm shadow-sky-500/20 group-hover:scale-105 transition">
            <Activity className="w-5 h-5 stroke-[2.5]" />
          </div>
          <div className="flex flex-col">
            <span className="text-lg font-black tracking-tight text-slate-900 leading-none">
              ClinicCare
            </span>
            <span className="text-[10px] text-slate-500 font-medium tracking-wide">
              Healthcare Platform
            </span>
          </div>
        </Link>

        {/* Auth CTA & Session Access */}
        <div className="flex items-center gap-3">
          {isAuthenticated && user ? (
            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                size="sm"
                leftIcon={<LayoutDashboard className="w-4 h-4" />}
                onClick={() => navigate(getDashboardLink())}
              >
                Go to Dashboard
              </Button>
              <div className="hidden sm:flex flex-col text-right">
                <span className="text-xs font-bold text-slate-900 truncate max-w-[140px]">{user.full_name}</span>
                <span className="text-[10px] text-sky-700 font-semibold uppercase tracking-wider">{user.role.replace('_', ' ')}</span>
              </div>
              <Button
                variant="ghost"
                size="sm"
                className="text-rose-600 hover:bg-rose-50"
                onClick={logout}
                title="Sign Out"
              >
                <LogOut className="w-4 h-4" />
              </Button>
            </div>
          ) : (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/onboard-clinic')}
                className="hidden sm:inline-flex text-emerald-700 hover:text-emerald-800 hover:bg-emerald-50 font-semibold"
              >
                Register Clinic
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/login')}
                className="text-slate-700 font-semibold"
              >
                Sign In
              </Button>
              <Button
                variant="primary"
                size="sm"
                leftIcon={<User className="w-3.5 h-3.5" />}
                onClick={() => navigate('/register')}
                className="shadow-sm shadow-sky-500/20 font-semibold"
              >
                Get Started
              </Button>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}

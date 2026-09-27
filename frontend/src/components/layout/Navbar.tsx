import React from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { Button } from '@/components/ui/Button'
import { Activity, User, LogOut, LayoutDashboard, Calendar, Sparkles } from 'lucide-react'

export const Navbar: React.FC = () => {
  const { user, isAuthenticated, logout } = useAuth()
  const navigate = useNavigate()

  const getDashboardLink = () => {
    if (!user) return '/login'
    if (user.role === 'ADMIN' || user.role === 'FRONT_DESK') return '/admin/dashboard'
    if (user.role === 'DOCTOR') return '/doctor/dashboard'
    return '/patient/dashboard'
  }

  return (
    <header className="sticky top-0 z-40 bg-white/90 backdrop-blur-md border-b border-slate-200/80 transition-all">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2.5 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-600 to-teal-500 flex items-center justify-center text-white shadow-md shadow-sky-500/20 group-hover:scale-105 transition">
            <Activity className="w-6 h-6 stroke-[2.5]" />
          </div>
          <div>
            <span className="text-xl font-black tracking-tight text-slate-900 flex items-center gap-1">
              ClinicCare <span className="text-xs px-2 py-0.5 rounded-md bg-sky-100 text-sky-700 font-bold">AI</span>
            </span>
          </div>
        </Link>

        {/* Navigation Links */}
        <nav className="hidden md:flex items-center gap-6 text-sm font-semibold text-slate-600">
          <Link to="/" className="hover:text-sky-600 transition">
            Home
          </Link>
          <Link to="/patient/doctors" className="hover:text-sky-600 transition">
            Doctors
          </Link>
          <Link to="/patient/appointments/book" className="hover:text-sky-600 transition flex items-center gap-1 text-sky-600">
            <Calendar className="w-4 h-4" /> Book
          </Link>
          <Link to="/patient/ambulance" className="hover:text-rose-600 transition flex items-center gap-1 text-rose-600 font-bold">
            Ambulance
          </Link>
          <Link to="/patient/blood" className="hover:text-pink-600 transition">
            Blood Bank
          </Link>
          <Link to="/patient/facilities" className="hover:text-sky-600 transition">
            Facilities
          </Link>
          <Link to="/patient/chat" className="hover:text-teal-600 transition flex items-center gap-1 text-teal-600">
            <Sparkles className="w-4 h-4" /> AI Assistant
          </Link>
        </nav>


        {/* Auth CTA */}
        <div className="flex items-center gap-3">
          {isAuthenticated && user ? (
            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                size="sm"
                leftIcon={<LayoutDashboard className="w-4 h-4" />}
                onClick={() => navigate(getDashboardLink())}
              >
                Dashboard
              </Button>
              <div className="hidden sm:flex flex-col text-right">
                <span className="text-xs font-bold text-slate-900">{user.full_name}</span>
                <span className="text-[10px] text-slate-500 uppercase tracking-wider">{user.role}</span>
              </div>
              <Button
                variant="ghost"
                size="sm"
                className="text-rose-600 hover:bg-rose-50"
                onClick={logout}
              >
                <LogOut className="w-4 h-4" />
              </Button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm" onClick={() => navigate('/login')}>
                Sign In
              </Button>
              <Button
                variant="primary"
                size="sm"
                leftIcon={<User className="w-4 h-4" />}
                onClick={() => navigate('/register')}
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

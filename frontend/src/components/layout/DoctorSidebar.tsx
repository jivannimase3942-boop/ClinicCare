import React from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import {
  LayoutDashboard,
  CalendarCheck,
  Clock,
  LogOut,
  Stethoscope,
} from 'lucide-react'
import { cn } from '@/lib/utils'

export const DoctorSidebar: React.FC = () => {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const links = [
    { to: '/doctor/dashboard', label: 'Doctor Dashboard', icon: LayoutDashboard },
    { to: '/doctor/appointments', label: 'Consultations', icon: CalendarCheck },
  ]

  return (
    <aside className="w-64 bg-white border-r border-slate-200/80 flex flex-col shrink-0 min-h-[calc(100vh-4rem)]">
      {/* User Card */}
      <div className="p-4 border-b border-slate-100 flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-teal-100 text-teal-700 flex items-center justify-center font-bold text-sm shrink-0">
          <Stethoscope className="w-5 h-5" />
        </div>
        <div className="overflow-hidden">
          <h4 className="text-sm font-bold text-slate-900 truncate">{user?.full_name}</h4>
          <span className="text-xs text-teal-700 font-medium">Physician Portal</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1">
        {links.map((link) => {
          const Icon = link.icon
          return (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.to === '/doctor/dashboard'}
              className={({ isActive }) =>
                cn(
                  'flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200',
                  isActive
                    ? 'bg-teal-50 text-teal-800 shadow-sm shadow-teal-100'
                    : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                )
              }
            >
              <div className="flex items-center gap-3">
                <Icon className="w-4 h-4 shrink-0" />
                <span>{link.label}</span>
              </div>
            </NavLink>
          )
        })}
      </nav>

      {/* Bottom */}
      <div className="p-3 border-t border-slate-100">
        <button
          onClick={() => {
            logout()
            navigate('/login')
          }}
          className="w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold text-rose-600 hover:bg-rose-50 transition"
        >
          <LogOut className="w-4 h-4" />
          <span>Sign Out</span>
        </button>
      </div>
    </aside>
  )
}

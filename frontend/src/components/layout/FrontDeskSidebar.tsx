import React from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import {
  LayoutDashboard,
  Users,
  CalendarDays,
  Stethoscope,
  Siren,
  Truck,
  AlertOctagon,
  LogOut,
  Building2,
  Ticket,
  Receipt,
} from 'lucide-react'
import { cn } from '@/lib/utils'

export const FrontDeskSidebar: React.FC = () => {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const links = [
    { to: '/frontdesk/dashboard', label: 'Reception Overview', icon: LayoutDashboard },
    { to: '/frontdesk/queue', label: 'OPD Queue & Tokens', icon: Ticket, badge: 'Live' },
    { to: '/frontdesk/billing', label: 'Billing & Receipts', icon: Receipt },
    { to: '/frontdesk/patients', label: 'Patient Lookup', icon: Users },
    { to: '/frontdesk/appointments', label: 'Appointment Desk', icon: CalendarDays },
    { to: '/frontdesk/doctors', label: 'Doctor Availability', icon: Stethoscope },
    { to: '/frontdesk/emergency', label: 'Emergency & Triage', icon: Siren, badge: 'Live' },
    { to: '/frontdesk/ambulances', label: 'Ambulance Fleet', icon: Truck },
    { to: '/frontdesk/escalations', label: 'Front-Desk Queue', icon: AlertOctagon, badge: 'Escalations' },
  ]

  return (
    <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col shrink-0 min-h-[calc(100vh-4rem)] border-r border-slate-800">
      {/* Header Info */}
      <div className="p-4 border-b border-slate-800 flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-amber-500/20 border border-amber-500/30 text-amber-400 flex items-center justify-center font-bold text-sm shrink-0">
          <Building2 className="w-5 h-5" />
        </div>
        <div className="overflow-hidden">
          <h4 className="text-sm font-bold text-white truncate">{user?.full_name}</h4>
          <span className="text-[10px] uppercase tracking-wider font-semibold text-amber-400 bg-amber-950/60 px-2 py-0.5 rounded border border-amber-800/40">
            Front Desk Desk
          </span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {links.map((link) => {
          const Icon = link.icon
          return (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.to === '/frontdesk/dashboard'}
              className={({ isActive }) =>
                cn(
                  'flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all duration-200',
                  isActive
                    ? 'bg-amber-600 text-white shadow-sm shadow-amber-900 font-semibold'
                    : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                )
              }
            >
              <div className="flex items-center gap-3">
                <Icon className="w-4 h-4 shrink-0" />
                <span>{link.label}</span>
              </div>
              {link.badge && (
                <span className="px-1.5 py-0.5 text-[10px] font-bold rounded-md bg-amber-500/20 text-amber-300 border border-amber-500/30">
                  {link.badge}
                </span>
              )}
            </NavLink>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="p-3 border-t border-slate-800">
        <button
          onClick={() => {
            logout()
            navigate('/login')
          }}
          className="w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold text-rose-400 hover:bg-rose-500/10 transition"
        >
          <LogOut className="w-4 h-4" />
          <span>Sign Out</span>
        </button>
      </div>
    </aside>
  )
}

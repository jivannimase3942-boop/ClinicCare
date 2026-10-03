import React from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import {
  LayoutDashboard,
  Calendar,
  UserCheck,
  FileText,
  MessageSquare,
  PhoneCall,
  Star,
  User,
  LogOut,
  Sparkles,
  HelpCircle,
  Truck,
  Droplet,
  Building2,
  BellRing,
  ClipboardCheck,
  Receipt,
  Activity,
  Pill,
} from 'lucide-react'
import { cn } from '@/lib/utils'

export const PatientSidebar: React.FC = () => {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const links = [
    { to: '/patient/dashboard', label: 'Overview', icon: LayoutDashboard },
    { to: '/patient/timeline', label: 'Medical Timeline', icon: Activity },
    { to: '/patient/prescriptions', label: 'My Prescriptions', icon: Pill },
    { to: '/patient/appointments', label: 'My Appointments', icon: Calendar },
    { to: '/patient/appointments/book', label: 'Book Appointment', icon: UserCheck },
    { to: '/patient/invoices', label: 'Invoices & Receipts', icon: Receipt },
    { to: '/patient/chat', label: 'AI Health Assistant', icon: Sparkles, badge: 'AI' },
    { to: '/patient/ambulance', label: 'Ambulance Dispatch', icon: Truck, badge: '24/7' },
    { to: '/patient/blood', label: 'Blood Bank & Requests', icon: Droplet },
    { to: '/patient/facilities', label: 'Healthcare Facilities', icon: Building2 },
    { to: '/patient/reports', label: 'Medical Reports', icon: FileText },
    { to: '/patient/visits', label: 'Visit History', icon: ClipboardCheck },
    { to: '/patient/reminders', label: 'Reminders & Follow-Ups', icon: BellRing },
    { to: '/patient/voice-request', label: 'Voice Callback', icon: PhoneCall },
    { to: '/patient/feedback', label: 'Rate & Feedback', icon: Star },
    { to: '/patient/profile', label: 'My Profile', icon: User },
  ]

  return (
    <aside className="w-64 bg-white border-r border-slate-200/80 flex flex-col shrink-0 min-h-[calc(100vh-4rem)]">
      {/* User Card */}
      <div className="p-4 border-b border-slate-100 flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-sky-100 text-sky-700 flex items-center justify-center font-bold text-sm shrink-0">
          {user?.full_name?.charAt(0) || 'P'}
        </div>
        <div className="overflow-hidden">
          <h4 className="text-sm font-bold text-slate-900 truncate">{user?.full_name}</h4>
          <p className="text-xs text-slate-500 truncate">{user?.email}</p>
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
              end={link.to === '/patient/dashboard'}
              className={({ isActive }) =>
                cn(
                  'flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200',
                  isActive
                    ? 'bg-sky-50 text-sky-700 shadow-sm shadow-sky-100'
                    : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                )
              }
            >
              <div className="flex items-center gap-3">
                <Icon className="w-4 h-4 shrink-0" />
                <span>{link.label}</span>
              </div>
              {link.badge && (
                <span className="px-1.5 py-0.5 text-[10px] font-bold rounded-md bg-teal-100 text-teal-800">
                  {link.badge}
                </span>
              )}
            </NavLink>
          )
        })}
      </nav>

      {/* Bottom Emergency Help & Logout */}
      <div className="p-3 border-t border-slate-100 space-y-2">
        <div className="bg-rose-50 border border-rose-200 rounded-xl p-3 text-xs text-rose-800">
          <p className="font-bold flex items-center gap-1.5 mb-1">
            <HelpCircle className="w-3.5 h-3.5 text-rose-600" /> Need Immediate Help?
          </p>
          <p className="text-[11px] text-rose-700">Dial emergency at 108 or hospital desk.</p>
        </div>

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

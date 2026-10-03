import React from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import {
  LayoutDashboard,
  Users,
  Stethoscope,
  Building2,
  CalendarDays,
  FileSpreadsheet,
  Star,
  AlertOctagon,
  PhoneCall,
  Bot,
  AlertTriangle,
  LogOut,
  ShieldCheck,
  Truck,
  Droplet,
  Siren,
  BellRing,
  Building,
  Hospital,
  IndianRupee,
  Pill,
} from 'lucide-react'
import { cn } from '@/lib/utils'

export const AdminSidebar: React.FC = () => {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const links = [
    { to: '/admin/dashboard', label: 'Dashboard Overview', icon: LayoutDashboard },
    { to: '/admin/clinic-profile', label: 'Clinic Settings & Profile', icon: Hospital },
    { to: '/admin/revenue', label: 'Revenue & Billing', icon: IndianRupee, badge: 'Finance' },
    { to: '/admin/pharmacy', label: 'Pharmacy & Stock', icon: Pill, badge: 'Rx' },
    { to: '/admin/audit-logs', label: 'Security & Audit Logs', icon: ShieldCheck, badge: 'Protected' },
    { to: '/admin/emergency', label: 'Emergency & Triage', icon: Siren, badge: 'Live' },
    { to: '/admin/ambulances', label: 'Ambulance Fleet', icon: Truck },
    { to: '/admin/blood-bank', label: 'Blood Bank & Requests', icon: Droplet },
    { to: '/admin/facilities', label: 'Facilities Directory', icon: Building },
    { to: '/admin/patients', label: 'Patient Directory', icon: Users },
    { to: '/admin/doctors', label: 'Doctors & Staff', icon: Stethoscope },
    { to: '/admin/departments', label: 'Departments', icon: Building2 },
    { to: '/admin/appointments', label: 'All Appointments', icon: CalendarDays },
    { to: '/admin/reminders', label: 'Follow-Up Reminders', icon: BellRing },
    { to: '/admin/reports', label: 'Reports Management', icon: FileSpreadsheet },
    { to: '/admin/feedback', label: 'Patient Reviews', icon: Star },
    { to: '/admin/escalations', label: 'Front-Desk Escalations', icon: AlertOctagon, badge: 'Critical' },
    { to: '/admin/voice-calls', label: 'Voice Callback Queue', icon: PhoneCall },
    { to: '/admin/conversations', label: 'AI Chat Logs', icon: Bot },
    { to: '/admin/errors', label: 'System Error Logs', icon: AlertTriangle },
  ]

  return (
    <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col shrink-0 min-h-[calc(100vh-4rem)] border-r border-slate-800">
      {/* Header Info */}
      <div className="p-4 border-b border-slate-800 flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-emerald-500/20 border border-emerald-500/30 text-emerald-400 flex items-center justify-center font-bold text-sm shrink-0">
          <Hospital className="w-5 h-5" />
        </div>
        <div className="overflow-hidden">
          <h4 className="text-sm font-bold text-white truncate">{user?.full_name}</h4>
          <div className="flex items-center gap-1.5 mt-0.5">
            <span className="text-[9px] uppercase tracking-wider font-semibold text-emerald-400 bg-emerald-950/60 px-1.5 py-0.5 rounded border border-emerald-800/40">
              {user?.role}
            </span>
            <span className="text-[10px] text-slate-400 truncate max-w-[90px]" title={user?.clinic_name || 'ClinicCare Central'}>
              {user?.clinic_name || 'ClinicCare Central'}
            </span>
          </div>
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
              end={link.to === '/admin/dashboard'}
              className={({ isActive }) =>
                cn(
                  'flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all duration-200',
                  isActive
                    ? 'bg-sky-600 text-white shadow-sm shadow-sky-900 font-semibold'
                    : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                )
              }
            >
              <div className="flex items-center gap-3">
                <Icon className="w-4 h-4 shrink-0" />
                <span>{link.label}</span>
              </div>
              {link.badge && (
                <span className="px-1.5 py-0.5 text-[10px] font-bold rounded-md bg-rose-500/20 text-rose-300 border border-rose-500/30">
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
